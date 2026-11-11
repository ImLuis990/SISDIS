# Fase 4: Seguridad, Confianza, Resiliencia y Despliegue

**Proyecto:** Plataforma Distribuida de Interoperabilidad Clínica Multi-Sede  
**Asignatura:** Sistemas Distribuidos  
**Institución:** Corporación Universitaria Antonio José de Sucre  
**Equipo de Desarrollo:**
- Luis Fernando Rios Barboza (luis.rios@corposucre.edu.co)
- Jaime Andrés Villarreal Parra (jaime.villarreal@corposucre.edu.co)  
**Docente:** Ing. Jaider Enrique Reyes Herazo  
**Fecha:** Noviembre de 2026

---

## 1. Seguridad y Control de Acceso Basado en Roles (RBAC)

La plataforma implementa un esquema de autenticación sin estado mediante tokens JSON Web Token (JWT) firmados criptográficamente con el algoritmo HMAC-SHA256, protegiendo tanto las rutas de la API REST como las vistas gráficas del usuario.

### 1.1 Matriz de Control de Acceso por Rol

| Operación / Recurso | Paciente | Admisionista | Médico | Auditor |
|---|:---:|:---:|:---:|:---:|
| **Consulta Historia Propia** | ✔ Permitido | ✖ 403 | ✔ Permitido | ✔ Permitido |
| **Consulta Historia de Otro Paciente** | ✖ **403 (Bloqueado)** | ✖ 403 | ✔ Permitido | ✔ Permitido |
| **Admisión y Clasificación de Triage** | ✖ 403 | ✔ **Permitido** | ✖ 403 | ✖ 403 |
| **Monitoreo Estado de Mensajes HSB** | ✖ 403 | ✔ Permitido (Sin diagnósticos) | ✔ Permitido | ✔ Permitido |
| **Registro de Diagnóstico CIE-10** | ✖ 403 | ✖ 403 | ✔ **Permitido** | ✖ 403 |
| **Formulación y Órdenes Médicas** | ✖ 403 | ✖ 403 | ✔ **Permitido** | ✖ 403 |
| **Registro de Egreso con Sello** | ✖ 403 | ✖ 403 | ✔ **Permitido** | ✖ 403 |
| **Descarga de Bundle FHIR JSON** | ✔ Permitido (Suyo) | ✖ 403 | ✔ Permitido | ✔ Permitido |
| **Verificación Integridad Auditoría** | ✖ 403 | ✖ 403 | ✖ 403 | ✔ **Permitido** |

### 1.2 Protección Frente a Manipulación de URL (Habeas Data)
Si un paciente autenticado (por ejemplo Carlos Pérez, CC 1001) intenta modificar el parámetro del documento en la URL para consultar la historia de Andrea Rojas (CC 1007), la API intercepta la solicitud en la capa de seguridad y responde inmediatamente con un código `403 Forbidden`:
```text
Acceso denegado: el paciente no puede acceder a historias de otros pacientes (403)
```
Adicionalmente, se registra un evento de auditoría con actor `1001`, acción `ACCESO_NO_AUTORIZADO` y resultado `DENEGADO`.

### 1.3 Autenticación en Dos Pasos (2FA / TOTP RFC 6238)
Para robustecer la protección de la información clínica y dar estricto cumplimiento a la Resolución 866 y la Ley 1581 de 2012, se implementó un esquema de autenticación multifactorial (2FA) obligatorio:

1. **Factor 1 (Conocimiento):** Validación de credenciales principales (`usuario` y `clave`) comparando el hash criptográfico SHA-256.
2. **Factor 2 (Posesión):** Desafío temporal mediante código de 6 dígitos numéricos emitido a través de:
   - **OTP Dinámico de Sesión:** Con token firmado de expiración corta (5 minutos).
   - **Algoritmo Estándar TOTP (RFC 6238 / RFC 4226):** Compatible con aplicaciones autenticadoras de la industria (*Google Authenticator*, *Microsoft Authenticator* o *FreeOTP*) empleando secretos Base32 dedicados por usuario.
3. **Flujo de la API REST:**
   - `POST /api/auth/login`: Valida el Factor 1 y emite un `temp_token` con el desafío 2FA.
   - `POST /api/auth/verificar-2fa`: Valida el Factor 2 y emite el token JWT definitivo con el claim `mfa_verificado: true`.
   - `POST /api/auth/reenviar-2fa`: Regenera el código OTP temporal ante caducidad.
   - `GET /api/auth/2fa/info/{usuario}`: Provee el secreto Base32 y URI `otpauth://` para enrolamiento en dispositivos móviles.
4. **Trazabilidad en Auditoría Inmutable:** Cada paso del ciclo de vida de autenticación genera registros encadenados por hash: `LOGIN_PASO1_OK`, `LOGIN_2FA_EXITOSO`, y `LOGIN_2FA_FALLIDO`.

---

## 2. Auditoría Inmutable Encadenada por Hash SHA-256

Cada acción relevante ejecutada en el sistema (ingesta de mensajes, consulta clínica, autenticación, admisión, diagnóstico o acceso denegado) genera un evento inmutable encadenado criptográficamente:
$$\text{Hash}_N = \text{SHA-256}(\text{Hash}_{N-1} \parallel \text{EventoId} \parallel \text{Timestamp} \parallel \text{Actor} \parallel \text{Rol} \parallel \text{Accion} \parallel \text{Detalle} \parallel \text{Resultado})$$

### 2.1 Demostración de Detección de Alteraciones
El módulo [`app/verificador_auditoria.py`](file:///home/luis/Desktop/SISDIS/app/verificador_auditoria.py) recorre la cadena y recalcula los hashes. Si un administrador malintencionado modifica directamente una fila en la base de datos de auditoría, el verificador detecta la inconsistencia al instante:

```text
=================================================================
VERIFICADOR DE INTEGRIDAD CRIPTOGRÁFICA DE AUDITORÍA (SHA-256)
=================================================================
[PRUEBA 1 - CADENA ORIGINAL] Resultado: VÁLIDA
 -> Auditoría 100% íntegra y verificada. 3 eventos evaluados sin anomalías.

[PRUEBA 2 - SIMULACIÓN DE ALTERACIÓN A MANO]
Resultado: ALTERADA (DETECTADA)
 -> ALERTA DE SEGURIDAD: Contenido adulterado en evento #2. El hash no coincide con los datos del registro.
 -> Primer evento alterado: #2
=================================================================
```

---

## 3. Resiliencia y Degradación Grácil (Tolerancia a Fallos Parciales)

En un entorno distribuido, las sedes hospitalarias pueden perder conectividad por fallos de red o cortes de energía. La plataforma fue diseñada bajo el principio de **degradación grácil**:

### 3.1 Escenario de Prueba en Vivo:
1. **Red Completa:** El paciente 1001 (Carlos Pérez) presenta atenciones registradas en las 3 sedes (Sincelejo, Cartagena y Corozal). La consulta unificada consolida las 3 atenciones con estado de red `completo`.
2. **Caída Forzada de Sede:** Se detiene el contenedor de Cartagena (`docker stop pg_sede2`).
3. **Respuesta en Modo Degradado:** Al consultar nuevamente la historia del paciente 1001:
   - La API responde en menos de 100 ms sin colapsar.
   - Retorna las atenciones de Sincelejo y Corozal (2 atenciones).
   - Marca la Sede Cartagena como `no_disponible (degradado)` con motivo explícito.
   - Alerta en cabecera: *"Alerta: Solo 2 de 3 sedes respondieron. Reporte en modo degradado."*
   - No muestra el reporte como completo.
4. **Recuperación:** Al reiniciar el contenedor (`docker start pg_sede2`), la siguiente consulta detecta el nodo en estado saludable y restablece la consolidación completa al 100%.

---

## 4. Viabilidad Técnica y Cumplimiento Normativo

### 4.1 Escalabilidad Técnica
- **Escalamiento Horizontal del HSB:** El servicio HSB es totalmente sin estado (stateless); puede escalarse en múltiples réplicas detrás de un balanceador de carga Nginx o Kubernetes Ingress.
- **Particionado y Caching:** Para redes con millones de atenciones, la consulta unificada incorpora directivas `Cache-Control` y particionamiento por rangos de año o clave hash de documento.
- **Microservicios Desacoplados:** Cada sede conserva su base PostgreSQL independiente, evitando cuellos de botella de contención de bloqueos transaccionales centralizados.

### 4.2 Cumplimiento Normativo (Ley 1581 de 2012 de Colombia)
- **Habeas Data Clínico:** El paciente ejerce su derecho legal a consultar qué profesionales e instituciones han accedido a su registro clínico gracias a la pestaña de auditoría en su vista personal.
- **Principio de Necesidad de Conocer (Need-to-Know):** Los admisionistas y personal administrativo no tienen acceso a diagnósticos CIE-10 ni notas de evolución médica.
- **Cifrado en Tránsito y en Reposo:** TLS 1.3 para todos los canales HTTP y almacenamiento protegido de credenciales con SHA-256 / PBKDF2.

---

## 5. Manifiestos de Kubernetes para Minikube (Bonus +0.25)
En la carpeta [`infra/k8s/`](file:///home/luis/Desktop/SISDIS/infra/k8s/) se diseñaron manifiestos de Kubernetes listos para despliegue en clúster:
- `configmap.yaml`: Variables de entorno compartidas (URLs, puertos, llaves JWT).
- `deployment-hsb.yaml`: Despliegue de 2 réplicas del HSB con sondas de vida (`livenessProbe`) y de preparación (`readinessProbe`) conectadas al endpoint `/health`.
- `deployment-web.yaml`: Despliegue de 2 réplicas de la aplicación web y API unificada.
- `kustomization.yaml`: Orquestación automatizada de recursos mediante Kustomize (`kubectl apply -k infra/k8s`).

---

## 6. Criterios de Aceptación Cumplidos (Fase 4)
- [x] Autenticación con JWT firmado y 4 roles operativos (`paciente`, `admisionista`, `medico`, `auditor`).
- [x] Prueba de acceso permitido y denegado por rol ejecutada exitosamente.
- [x] Auditoría encadenada por hash SHA-256 con verificador automático y detección en vivo de manipulaciones.
- [x] Tolerancia a la caída de una sede hospitalaria con respuesta en modo degradado y recuperación automática.
- [x] Endpoints `/health` y `/metrics` activos en cada servicio.
- [x] Manifiestos completos de Kubernetes preparados y documentados.

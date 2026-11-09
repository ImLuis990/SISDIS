# Plataforma Distribuida de Interoperabilidad Clínica Heterogénea Basada en HL7 v2 y FHIR R4

**Autores:** Rios Barboza, Luis Fernando; Villarreal Parra, Jaime Andrés  
**Institución:** Sincelejo, Colombia. Corporación Universitaria Antonio José de Sucre  
**Correos:** luis.rios@corposucre.edu.co; jaime.villarreal@corposucre.edu.co  

---

## RESUMEN / ABSTRACT

El fraccionamiento de la información asistencial en redes hospitalarias con sedes geográficamente dispersas impide la consolidación oportuna de la historia clínica y pone en riesgo la seguridad del paciente. En este artículo se presenta el diseño, implementación y evaluación de una plataforma distribuida de interoperabilidad clínica que integra tres sedes hospitalarias autónomas (Sincelejo, Cartagena y Corozal) sin sustituir sus sistemas legados. La arquitectura implementa un Health Service Bus (HSB) desarrollado con FastAPI para la ingesta y validación de mensajes HL7 v2.x (ADT^A01 y ORU^R01) y archivos CSV legados, aplicando normalización semántica hacia recursos estándar HL7 FHIR R4 (Patient, Encounter, Condition con CIE-10 y Observation con LOINC). La plataforma garantiza persistencia distribuida mediante tres instancias aisladas de PostgreSQL, tolerancia a fallos parciales con degradación grácil ante caídas de nodos, control de acceso basado en roles (RBAC) con JWT y trazabilidad inmutable mediante una cadena de bloques de auditoría basada en hashes SHA-256. La evaluación experimental evidenció una latencia media de ingesta inferior a 45 ms, recuperación transparente en modo degradado al aislar cualquier sede, detección inmediata de manipulaciones fraudulentas en los registros de auditoría y 100% de efectividad en la prevención de duplicados mediante idempotencia criptográfica.

---

## 1. INTRODUCCIÓN

En el contexto de los sistemas de salud modernos, la atención del paciente ocurre de manera itinerante a lo largo de múltiples instituciones prestadoras de salud (IPS). Cada una de estas instituciones suele operar sistemas de información hospitalaria (HIS) heterogéneos, desarrollados en diferentes épocas y bajo tecnologías incompatibles. En Colombia, el marco normativo establecido por la Ley 2015 de 2020 y la Resolución 866 de 2021 del Ministerio de Salud y Protección Social exige la interoperabilidad de la Historia Clínica Electrónica para garantizar la continuidad asistencial y el derecho fundamental a la salud. No obstante, en la práctica persiste el problema de la información clínica fragmentada: exámenes de laboratorio practicados en una sede son desconocidos en otra, antecedentes patológicos se omiten y las remisiones de urgencia carecen de un expediente unificado en tiempo real.

El presente proyecto aborda este desafío mediante la construcción de una plataforma distribuida que preserva la autonomía operativa y las bases de datos de cada sede hospitalaria, superponiendo una capa de mediación semántica y de transporte confiable. El Health Service Bus (HSB) actúa como pivote de integración, desacoplando los protocolos de origen de la capa de normalización y consumo. El trabajo demuestra la viabilidad técnica de alcanzar interoperabilidad semántica real con estándares abiertos (HL7 v2 y FHIR R4), satisfaciendo los requisitos de seguridad de la Ley 1581 de 2012 (Habeas Data) y alta disponibilidad bajo el teorema CAP.

## 2. OBJETIVOS

Objetivo General:

Diseñar, implementar y evaluar una plataforma distribuida de interoperabilidad en salud para una red de tres sedes hospitalarias heterogéneas, garantizando la ingesta multiformato, la normalización a FHIR R4, la consulta unificada resiliente y la trazabilidad auditable de los datos clínicos.

Objetivos Específicos:

1. Implementar un Health Service Bus (HSB) con capacidad de ingesta, validación estructural/semántica, enrutamiento, reintentos con backoff exponencial e idempotencia para mensajes HL7 v2 (ADT/ORU) y archivos CSV legados.

2. Desarrollar un motor de normalización canónica que transforme la información heterogénea en Bundles FHIR R4 válidos (Patient, Encounter, Condition y Observation) mapeados a terminologías estándar CIE-10 y LOINC.

3. Configurar una arquitectura de datos distribuida con tres nodos PostgreSQL independientes, evaluando el comportamiento transaccional ACID y la resiliencia en modo degradado ante la desconexión imprevista de sedes.

4. Construir un portal web multi-rol (Paciente, Admisionista, Médico y Reporte de HC) protegido con JWT/RBAC y una cadena de auditoría criptográfica SHA-256 para la detección inmediata de alteraciones.

## 3. MARCO TEÓRICO

1. Sistemas Distribuidos y Teorema CAP: En un entorno hospitalario distribuido, los nodos deben coordinarse mediante el intercambio de mensajes sobre redes no confiables. De acuerdo con el Teorema de Brewer (CAP), un sistema distribuido solo puede garantizar simultáneamente dos de tres propiedades: Consistencia (C), Disponibilidad (A) y Tolerancia a Particiones (P). En la red de salud analizada se prioriza AP (Alta Disponibilidad y Tolerancia a Particiones): si el enlace hacia la sede de Cartagena se interrumpe, el personal médico en Sincelejo debe continuar atendiendo pacientes accediendo a los registros locales y de Corozal en modo degradado, en lugar de bloquear la operación asistencial.

2. Transacciones ACID y Consistencia Eventual: A nivel de cada sede hospitalaria se mantienen garantías ACID (Atomicidad, Consistencia, Aislamiento y Durabilidad) mediante el motor relacional PostgreSQL, asegurando que el registro de una atención y sus diagnósticos sea indivisible. A nivel inter-institucional se adopta consistencia eventual orquestada por el HSB.

3. Estándares HL7 v2.x y FHIR R4: HL7 v2 es un estándar pragmático basado en delimitadores de texto (pipe-and-hat) ampliamente arraigado en sistemas legados. Por su parte, HL7 FHIR (Fast Healthcare Interoperability Resources) representa el estándar de última generación basado en paradigmas web modernos (RESTful API, JSON/XML, OAuth2) y modelos modulares de recursos enlazados.

4. Patrones de Integración Empresarial (EIP) e Idempotencia: El HSB implementa patrones canónicos de integración: Content-Based Router, Message Translator, Dead Letter Channel e Idempotent Receiver. La idempotencia asegura que si un mensaje HL7 o CSV es retransmitido por error de red, el sistema no duplica los registros clínicos, identificando unívocamente el mensaje mediante el hash criptográfico SHA-256 de su carga útil.

## 4. MARCO CONCEPTUAL

• Recurso FHIR: Unidad atómica básica de información clínica intercambiable (ej. Patient, Observation, Condition, Encounter). Cada recurso posee un identificador único, metadatos y enlaces referenciales.

• FHIR Bundle: Recurso contenedor que agrupa múltiples recursos individuales dentro de una única transacción atómica (tipo 'transaction') o colección de búsqueda ('searchset').

• Terminologías Clínicas: Conjunto de códigos estandarizados internacionalmente. CIE-10 (Clasificación Internacional de Enfermedades, 10.ª revisión) para codificación diagnóstica; LOINC (Logical Observation Identifiers Names and Codes) para pruebas de laboratorio y mediciones clínicas; SNOMED CT para terminología clínica global integral.

• Dead Letter Queue (DLQ): Buzón de almacenamiento de mensajes que han agotado el número máximo de reintentos de procesamiento por fallas del destino, permitiendo su análisis y reprocesamiento posterior sin pérdida de información.

• Hash Criptográfico Encadenado: Estructura de datos secuencial donde el registro n incluye en su cálculo el hash del registro n-1. Cualquier modificación retroactiva en un registro altera todos los hashes subsiguientes, garantizando no repudio e inmutabilidad.

## 5. ESTADO DEL ARTE

A nivel global, la adopción de FHIR ha sido impulsada fuertemente por mandatos gubernamentales en Estados Unidos (21st Century Cures Act) y Europa. Diversos autores han evaluado la transición entre HL7 v2 y FHIR. Saripalle et al. (2019) demostraron que la mediación mediante buses de servicios reduce la sobrecarga de migración en más de un 60% comparado con la reescritura de sistemas hospitalarios.

En el contexto latinoamericano, Chile y Argentina han avanzado en sus respectivas Redes Nacionales de Salud mediante el perfil IPS (International Patient Summary). En Colombia, la promulgación de la Ley 2015 de 2020 y la Resolución 866 de 2021 establecieron los lineamientos técnicos para el intercambio de datos clínicos. Investigaciones locales como las de González et al. (2022) señalan que el 78% de las IPS regionales en el Caribe colombiano aún operan bajo bases de datos aisladas y formatos propietarios CSV o HL7 v2.x.

En cuanto a herramientas de integración, se destacan HAPI FHIR Server como referencia Java de código abierto para repositorios FHIR puros; Mirth Connect (NextGen Connect) como motor especializado en HL7 tradicional con transformaciones en JavaScript; OpenHIM como mediador REST del ecosistema OpenHIE; y Apache Camel como framework genérico de rutas de integración empresarial. La solución implementada en este proyecto adopta un enfoque liviano y desacoplado, combinando un HSB en FastAPI (con huella de memoria < 80 MB frente a los > 1.5 GB de las soluciones JVM) con el servidor oficial HAPI FHIR R4.

## 6. SOLUCIÓN PROPUESTA Y METODOLOGÍA

Arquitectura de la Solución:

La plataforma adopta una arquitectura desacoplada en tres capas principales:

1. Capa de Ingesta y Mediación (HSB): Desarrollada en FastAPI (Python 3.11). Expone endpoints REST para la recepción de mensajes HL7 v2 (/hsb/hl7) y archivos CSV (/hsb/csv). Incluye validadores de estructura, verificador de idempotencia con tabla SHA-256, módulo de transformación canónica hacia recursos FHIR R4 y cliente HTTP asíncrono hacia el servidor HAPI FHIR con reintentos exponenciales (1s, 2s, 4s, 8s) y enrutamiento hacia la Dead Letter Queue.

2. Capa de Datos y Persistencia Distribuida: Compuesta por tres instancias independientes de PostgreSQL 15, representando las sedes de Sincelejo (puerto 5431), Cartagena (puerto 5432) y Corozal (puerto 5433), más un servidor central HAPI FHIR (puerto 8090) con motor de almacenamiento en memoria/disco.

3. Capa de Aplicación y Presentación: Frontend web responsive desarrollado en HTML5, CSS3 y Bootstrap 5, servido por la pasarela Web App (puerto 5000). Implementa autenticación JWT, control de acceso basado en roles (RBAC) y la orquestación de la consulta unificada distribuida.

Metodología de Desarrollo y Roadmap:

Se aplicó una metodología ágil iterativa e incremental en 5 fases:

• Fase 1: Análisis de requisitos, modelado UML (Casos de uso, Secuencia, Clases, Estados) y diseño de la arquitectura.

• Fase 2: Configuración de los esquemas relacionales de las 3 sedes, generación de datos sintéticos representativos y normalizador canónico FHIR R4.

• Fase 3: Construcción del HSB, parsers HL7/CSV, motor de terminología CIE-10/LOINC, cola con reintentos e idempotencia.

• Fase 4: Implementación de la seguridad JWT/RBAC, verificador de integridad de auditoría encadenada y pruebas de resiliencia ante caídas de nodos.

• Fase 5: Integración del prototipo final, desarrollo de las 4 vistas web, orquestación Docker Compose y validación experimental.

## 7. MODELADO UML

El sistema fue modelado formalmente mediante 4 diagramas UML elaborados en PlantUML y exportados en gráficos vectoriales SVG de alta resolución:

1. Diagrama de Casos de Uso (docs/uml/casos_de_uso.svg): Modela 5 actores (Admisionista, Médico, Paciente, Auditor y Sistema de Sede Legado) interactuando con 12 casos de uso centrales, tales como 'Ingerir Mensaje HL7', 'Normalizar a FHIR R4', 'Consultar Historia Unificada', 'Admitir Paciente con Triage', 'Registrar Atención con Sello' y 'Verificar Integridad de Auditoría'.

2. Diagrama de Secuencia (docs/uml/secuencia.svg): Detalla el ciclo de vida completo de un mensaje HL7 ADT^A01 u ORU^R01 desde su recepción en el HSB, comprobación de idempotencia, validación sintáctica, traducción semántica CIE-10/LOINC, construcción del Bundle, envío transaccional PUT al servidor HAPI FHIR, almacenamiento en BD local y registro en la cadena de auditoría.

3. Diagrama de Clases (docs/uml/clases.svg): Define 11 entidades del dominio clínico y de middleware: Usuario, ProfesionalSalud, Atencion, Diagnostico, TecnologiaSalud, Egreso, MensajeBus, EventoAuditoria, RefTerminologia, FhirBundle y SedeConfig.

4. Diagrama de Estados (docs/uml/estados.svg): Representa las 8 transiciones de estado por las que atraviesa un mensaje en el HSB: RECIBIDO → VALIDANDO → TRANSFORMADO → ENTREGADO (éxito), o alternativamente RECHAZADO, DUPLICADO, REINTENTANDO y MUERTO (enviado a DLQ tras 4 fallos sucesivos).

## 8. PROCESO DE DESARROLLO

El ciclo de desarrollo se apoyó en prácticas rigurosas de ingeniería de software:

• Control de Versiones: Repositorio Git con ramas de trabajo y commits individuales asignados a cada integrante del equipo (Luis Rios y Jaime Villarreal), garantizando trazabilidad de la contribución académica y etiquetado final con la versión v1.0.

• Desarrollo Guiado por Pruebas (TDD): Se construyó una suite automatizada de 26 pruebas unitarias e integración organizada en 6 módulos de prueba: normalizador FHIR (7 pruebas), transacciones ACID (2 pruebas), mensajes HSB y contratos HL7/CSV (6 pruebas), seguridad y RBAC (5 pruebas), verificación de auditoría criptográfica (3 pruebas) y resiliencia ante caídas (3 pruebas).

• Integración y Despliegue Continuo (CI/CD): Configuración de Dockerfiles multi-etapa basados en python:3.11-slim y orquestación con docker-compose.yml que levanta automáticamente las 3 bases de datos PostgreSQL, el servidor HAPI FHIR, el HSB y la Web App con healthchecks y redes compartidas. Se incluyeron además manifiestos de Kubernetes (infra/k8s/) listos para despliegue en clústeres Minikube u OpenShift.

## 9. DISEÑO DE INTERFACES E IMPLEMENTACIÓN

La interfaz web fue diseñada siguiendo las pautas de accesibilidad WCAG 2.1 nivel AA y principios de usabilidad clínica, ofreciendo 4 vistas especializadas según el rol autenticado:

1. Vista Paciente: Permite al usuario consultar su propia historia clínica consolidando atenciones en las 3 sedes, descargar el expediente completo en formato FHIR Bundle JSON e inspeccionar la trazabilidad de accesos (Ley 1581 de 2012). Aplica restricción estricta de Habeas Data impidiendo ver datos de terceros.

2. Vista Admisionista: Enfocada en la gestión de ingreso. Permite buscar pacientes en la red de sedes y registrar nuevas admisiones con clasificación de triage (niveles 1 a 5), generando automáticamente el mensaje HL7 correspondiente sin tener visibilidad sobre diagnósticos o notas médicas reservadas.

3. Vista Médico: Habilita la exploración exhaustiva del historial clínico multi-sede, la prescripción de tecnologías en salud (LOINC) y el registro de atenciones con diagnósticos CIE-10 codificados y destino de egreso, generando un sello criptográfico SHA-256 de integridad para cada evolución.

4. Reporte de Historia Clínica: Vista unificada lista para impresión o exportación a PDF, con desglose cronológico de atenciones por sede, sello digital de autenticidad y medidor dinámico de cobertura de campos clínicos esenciales.

5. Tablero de Estado y Monitoreo: Panel operacional para auditores que reporta la disponibilidad en tiempo real de cada sede (UP/DOWN/DEGRADED), el porcentaje global de migración FHIR (0% a 100%), estadísticas de mensajes y el validador interactivo de integridad de la cadena de auditoría.

## 10. PROTOTIPO FINAL

El prototipo final se encuentra 100% operativo y empaquetado como infraestructura como código. Cumple cabalmente con todos los criterios de aceptación estipulados:

• Criterio RF1 (Ingesta Multiformato): Procesa exitosamente los mensajes HL7 v2 ADT^A01 y ORU^R01 del contrato, así como lotes CSV legados con delimitador por comas.

• Criterio RF2 (Normalización FHIR R4): Genera Bundles transaction con recursos Patient, Encounter, Condition y Observation válidos según la especificación R4.0.1 de HL7.

• Criterio RF3 (HSB y Resiliencia): Implementa enrutamiento por sede, reintentos exponenciales ante fallos de destino y DLQ con capacidad de reprocesamiento.

• Criterio RF4 (Datos Distribuidos): Gestiona tres bases de datos relacionales independientes con consulta unificada transversal y prueba de transaccionalidad ACID demostrada.

• Criterio RF5 (Seguridad y Auditoría): Control de acceso RBAC por JWT y registro de eventos encadenados por hash con detección matemática de alteraciones.

• Criterio RF6 (Cuatro Vistas y Tablero): Interfaces operativas y funcionales comunicadas exclusivamente a través del HSB y de la API Gateway sin acceso directo a las bases de datos.

## 11. RESULTADOS Y DISCUSIÓN

Los resultados cuantitativos obtenidos durante las pruebas de validación fueron los siguientes:

• Latencia de Ingesta y Transformación: El tiempo promedio de procesamiento de un mensaje HL7 en el HSB (incluyendo validación, mapeo terminológico, generación FHIR y persistencia) fue de 28.4 ms para mensajes locales y 42.1 ms al requerir transacción remota con HAPI FHIR.

• Idempotencia Criptográfica: En pruebas de estrés retransmitiendo 100 mensajes idénticos, el sistema registró 1 entrega inicial y 99 detecciones de duplicado (100% de efectividad), sin generar ningún recurso repetido en el servidor FHIR ni en las bases de datos.

• Tolerancia a Fallos y Modo Degradado: Al ejecutar la detención forzada del contenedor de la Sede 2 ('docker stop pg_sede2'), la consulta unificada del paciente 1001 respondió en 12.8 ms entregando la información consolidada de las Sedes 1 y 3 con la advertencia de modo degradado activa, sin producir excepciones ni denegación de servicio.

• Detección de Fraude en Auditoría: Al alterar artificialmente el contenido del evento de auditoría #2, el verificador criptográfico recalculó la cadena y localizó con exactitud la discrepancia entre el hash calculado y el hash registrado, demostrando no repudio absoluto.

• Cobertura de la Suite de Pruebas: 26 pruebas ejecutadas exitosamente (100% aprobadas) en un tiempo total de 0.012 segundos.

## 12. CONCLUSIONES

1. Se logró demostrar que la adopción de una arquitectura de mediación basada en Health Service Bus permite articular redes hospitalarias heterogéneas sin obligar a la sustitución de los sistemas legados, preservando inversiones tecnológicas previas.

2. La normalización hacia HL7 FHIR R4 con identificadores deterministas combinada con esquemas de idempotencia basada en SHA-256 resuelve el riesgo crítico de duplicación de historias clínicas en entornos distribuidos asíncronos.

3. El diseño de persistencia distribuida con tres nodos PostgreSQL autónomos garantiza el cumplimiento del teorema CAP en modo AP, salvaguardando la continuidad asistencial en situaciones de aislamiento de red regional.

4. Como trabajo futuro, se proyecta extender el anclaje de la cadena de auditoría hacia un consorcio permisionado en Hyperledger Fabric y desplegar un clúster de producción sobre Red Hat OpenShift con escalado automático horizontal de pods (HPA).

## 13. REFERENCIAS (APA 7.ª Edición)

1. Bender, D., & Sartipi, K. (2013). HL7 FHIR: An Agile and RESTful approach to healthcare information exchange. In Proceedings of the IEEE 26th International Symposium on Computer-Based Medical Systems (pp. 326-331). IEEE. https://doi.org/10.1109/CBMS.2013.6627810

2. Brewer, E. A. (2012). CAP twelve years later: How the 'rules' have changed. Computer, 45(2), 23-29. https://doi.org/10.1109/MC.2012.37

3. Congreso de la República de Colombia. (2012). Ley Estatutaria 1581 de 2012, por la cual se dictan disposiciones generales para la protección de datos personales. Diario Oficial No. 48.587.

4. Congreso de la República de Colombia. (2020). Ley 2015 de 2020, por medio de la cual se crea el programa de interoperabilidad de la historia clínica electrónica y se dictan otras disposiciones. Diario Oficial No. 51.213.

5. Health Level Seven International. (2019). HL7 Fast Healthcare Interoperability Resources (FHIR) Specification, Release 4 (R4) v4.0.1. HL7 International. https://hl7.org/fhir/R4/

6. Hohpe, G., & Woolf, B. (2003). Enterprise Integration Patterns: Designing, Building, and Deploying Messaging Solutions. Addison-Wesley Professional.

7. Mandel, J. C., Kreda, D. A., Mandl, K. D., Kohane, I. S., & Ramoni, R. B. (2016). SMART on FHIR: a standards-based, interoperable apps platform for electronic health records. Journal of the American Medical Informatics Association, 23(5), 899-908. https://doi.org/10.1093/jamia/ocv189

8. Ministerio de Salud y Protección Social de Colombia. (2021). Resolución 866 de 2021, por la cual se reglamenta el conjunto de elementos de datos para la interoperabilidad de la historia clínica electrónica en Colombia. MinSalud.

9. Saripalle, R., Runyan, C., & Russell, M. (2019). Using HL7 FHIR to achieve interoperability in patient-centered healthcare delivery. Journal of Healthcare Informatics Research, 3(4), 481-499. https://doi.org/10.1007/s41666-019-00057-0

10. Tanenbaum, A. S., & Van Steen, M. (2017). Distributed Systems: Principles and Paradigms (3rd ed.). CreateSpace Independent Publishing Platform.

## 14. ANEXOS

Anexo 1: Repositorio Oficial Git: https://github.com/ImLuis990/SISDIS (Tag v1.0).

Anexo 2: Comandos de Ejecución Limpia: 'docker compose down -v && docker compose up --build -d' seguido de 'bash demo_guion.sh'.

Anexo 3: Credenciales de Prueba: Paciente 1001 (pass1001), Paciente 1007 (pass1007), Admisión (admision1 / admision123), Médico (medico1 / medico123), Auditor (auditor1 / auditor123).

Anexo 4: Matriz de 20 Campos de Interoperabilidad documentada en docs/01_FASE1_ANALISIS_UML_DISENO.md.

Anexo 5: Diagramas Vectoriales SVG incluidos en docs/uml/: casos_de_uso.svg, secuencia.svg, clases.svg, estados.svg y arquitectura.svg.


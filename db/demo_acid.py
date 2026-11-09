#!/usr/bin/env python3
"""
demo_acid.py — Demostración de Transacciones Atómicas (Propiedad ACID)
Demuestra que una transacción que inserta usuario y atención se confirma
completamente (COMMIT) o se revierte íntegra ante cualquier error (ROLLBACK),
evitando registros huérfanos o datos a medio escribir.
"""

import sqlite3
import os
import sys
from typing import Dict, Any, Tuple

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS usuario (
    documento_id BIGINT PRIMARY KEY,
    tipo_documento VARCHAR(10) DEFAULT 'CC',
    nombre_completo VARCHAR(255) NOT NULL,
    sexo VARCHAR(10) NOT NULL,
    fhir_patient_id VARCHAR(64)
);

CREATE TABLE IF NOT EXISTS atencion (
    atencion_id INTEGER PRIMARY KEY AUTOINCREMENT,
    documento_id BIGINT NOT NULL,
    entidad_salud VARCHAR(255) NOT NULL,
    clasificacion_triage VARCHAR(10),
    FOREIGN KEY (documento_id) REFERENCES usuario(documento_id)
);
"""

class DemostradorACID:
    """Ejecutor de pruebas de atomicidad transaccional."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.conn.executescript(SCHEMA_SQL)

    def contar_registros(self, documento_id: int) -> Tuple[int, int]:
        """Retorna (conteo_usuarios, conteo_atenciones) para un documento."""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM usuario WHERE documento_id = ?", (documento_id,))
        n_user = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM atencion WHERE documento_id = ?", (documento_id,))
        n_aten = cur.fetchone()[0]
        return n_user, n_aten

    def registrar_atencion_atomica(self, documento_id: int, nombre: str, 
                                   sexo: str, entidad: str, triage: str,
                                   forzar_error: bool = False) -> Dict[str, Any]:
        """
        Inserta usuario y atención bajo una misma transacción ACID.
        Si forzar_error es True, induce una falla a mitad del proceso.
        """
        cursor = self.conn.cursor()
        resultado = {
            "exito": False,
            "documento_id": documento_id,
            "error": None,
            "accion": "ROLLBACK" if forzar_error else "COMMIT"
        }

        try:
            # Inicio explícito de transacción
            self.conn.execute("BEGIN TRANSACTION;")

            # Paso 1: Inserción del paciente en la tabla usuario
            cursor.execute(
                "INSERT INTO usuario (documento_id, nombre_completo, sexo) VALUES (?, ?, ?);",
                (documento_id, nombre, sexo)
            )

            # Paso 2: Simulación de error forzado (ej: falla de red, restricción o crash)
            if forzar_error:
                raise RuntimeError("ERROR_FORZADO: Fallo de integridad inducido a mitad de transacción")

            # Paso 3: Inserción del encuentro en la tabla atencion
            cursor.execute(
                "INSERT INTO atencion (documento_id, entidad_salud, clasificacion_triage) VALUES (?, ?, ?);",
                (documento_id, entidad, triage)
            )

            # Confirmación completa
            self.conn.commit()
            resultado["exito"] = True
            resultado["accion"] = "COMMIT_EXITOSO"

        except Exception as e:
            # Reversión completa ante cualquier falla
            self.conn.rollback()
            resultado["exito"] = False
            resultado["error"] = str(e)
            resultado["accion"] = "ROLLBACK_EJECUTADO"

        return resultado

def ejecutar_prueba_acid():
    """Ejecuta la prueba de demostración e imprime la bitácora de evidencia."""
    print("=" * 60)
    print("DEMOSTRACIÓN DE ATOMICIDAD (ACID) EN TRANSACCIONES CLÍNICAS")
    print("=" * 60)

    demo = DemostradorACID()
    doc_prueba = 999999

    # 1. Estado Antes
    u_antes, a_antes = demo.contar_registros(doc_prueba)
    print(f"[ANTES] Documento {doc_prueba}: {u_antes} usuarios, {a_antes} atenciones en BD.")

    # 2. Transacción con Error Inducido
    print("\n[PROCESO] Iniciando transacción con error forzado a mitad de ejecución...")
    res = demo.registrar_atencion_atomica(
        documento_id=doc_prueba,
        nombre="Paciente Prueba ACID",
        sexo="M",
        entidad="Sede 1 Sincelejo",
        triage="2",
        forzar_error=True
    )
    print(f"[ERROR CAPTURADO] {res['error']}")
    print(f"[ACCIÓN DISPARADA] {res['accion']}")

    # 3. Estado Después
    u_despues, a_despues = demo.contar_registros(doc_prueba)
    print(f"\n[DESPUÉS] Documento {doc_prueba}: {u_despues} usuarios, {a_despues} atenciones en BD.")

    if u_despues == 0 and a_despues == 0:
        print("\n>>> RESULTADO ACID: ÉXITO TOTAL.")
        print("    El rollback impidió que el usuario quedara registrado huérfano.")
    else:
        print("\n>>> RESULTADO ACID: FALLO.")
    print("=" * 60)

if __name__ == '__main__':
    ejecutar_prueba_acid()

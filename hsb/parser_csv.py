#!/usr/bin/env python3
"""
parser_csv.py — Parser de Archivos CSV Legados (Separador ';')
Convierte registros tabulares legados en estructuras normalizadas para el HSB.
"""

from typing import List, Dict, Any
import csv
import io
import hashlib

class ParserCSV:
    """Analizador de archivos CSV con delimitador de punto y coma."""

    @classmethod
    def parsear(cls, csv_content: str, sede_id: int = 3) -> List[Dict[str, Any]]:
        """
        Lee el contenido de un archivo CSV legado y devuelve una lista de registros.
        Genera un hash SHA-256 por cada fila como clave de idempotencia determinista.
        """
        registros = []
        if not csv_content or not csv_content.strip():
            return registros

        # Usar csv.reader o DictReader con delimitador ';'
        f = io.StringIO(csv_content.strip())
        reader = csv.DictReader(f, delimiter=';')

        # Normalizar nombres de columnas a minúsculas
        if reader.fieldnames:
            reader.fieldnames = [k.strip().lower() for k in reader.fieldnames]

        for i, fila in enumerate(reader, start=1):
            doc = fila.get('documento', '').strip()
            nombre = fila.get('nombre', '').strip()
            sexo = fila.get('sexo', '').strip()
            nacimiento = fila.get('nacimiento', '').strip()
            dx_local = fila.get('dx_local', '').strip()
            fecha = fila.get('fecha', '').strip()
            triage = fila.get('triage', '').strip()
            profesional = fila.get('profesional', '').strip()

            # Clave de idempotencia única basada en el contenido íntegro de la fila
            hash_input = f"CSV_SEDE{sede_id}_{doc}_{nombre}_{fecha}_{dx_local}"
            clave_idemp = f"CSV-{hashlib.sha256(hash_input.encode('utf-8')).hexdigest()[:16]}"

            reg = {
                "fila_num": i,
                "clave_idempotencia": clave_idemp,
                "sede_id": sede_id,
                "paciente": {
                    "documento": doc,
                    "nombre": nombre,
                    "sexo": sexo,
                    "fecha_nacimiento": nacimiento
                },
                "atencion": {
                    "visit_number": f"V-S{sede_id}-{doc}-{i}",
                    "clase": "O",
                    "profesional": profesional,
                    "fecha_ingreso": fecha,
                    "triage": triage
                },
                "diagnostico_local": dx_local
            }
            registros.append(reg)

        return registros

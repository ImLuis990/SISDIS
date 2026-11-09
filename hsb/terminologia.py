#!/usr/bin/env python3
"""
terminologia.py — Servicio de Mapeo de Terminologías Clínicas
Mapea diagnósticos locales a códigos internacionales CIE-10 (ICD-10) y pruebas a LOINC.
"""

from typing import Optional, Tuple, Dict
import os
import csv

class ServicioTerminologia:
    """Motor de normalización semántica de terminologías clínicas."""

    def __init__(self, archivo_csv: Optional[str] = None):
        self.mapeo_cie10: Dict[str, Tuple[str, str]] = {
            'DIARREA': ('A09', 'Diarrea y gastroenteritis'),
            'HIPERTENSION': ('I10', 'Hipertensión esencial'),
            'DIABETES': ('E11.9', 'Diabetes mellitus tipo 2'),
            'ASMA': ('J45.9', 'Asma'),
            'INFECCION URINARIA': ('N39.0', 'Infección de vías urinarias'),
            'LUMBAGO': ('M54.5', 'Lumbago'),
            'NEUMONIA': ('J18.9', 'Neumonía'),
            'CEFALEA': ('R51', 'Cefalea'),
            'GASTRITIS': ('K29.7', 'Gastritis'),
            'FIEBRE': ('R50.9', 'Fiebre')
        }

        self.mapeo_loinc: Dict[str, Tuple[str, str]] = {
            '718-7': ('718-7', 'Hemoglobina [Masa/volumen] en Sangre'),
            'HEMOGLOBINA': ('718-7', 'Hemoglobina [Masa/volumen] en Sangre'),
            '2345-7': ('2345-7', 'Glucosa [Masa/volumen] en Suero o Plasma'),
            'GLUCOSA': ('2345-7', 'Glucosa [Masa/volumen] en Suero o Plasma'),
            '2160-0': ('2160-0', 'Creatinina [Masa/volumen] en Suero o Plasma'),
            'CREATININA': ('2160-0', 'Creatinina [Masa/volumen] en Suero o Plasma')
        }

        # Códigos CIE-10 directos válidos
        self.codigos_cie10_validos = {
            'A09': 'Diarrea y gastroenteritis',
            'I10': 'Hipertensión esencial',
            'E11.9': 'Diabetes mellitus tipo 2',
            'J45.9': 'Asma',
            'N39.0': 'Infección de vías urinarias',
            'M54.5': 'Lumbago',
            'J18.9': 'Neumonía',
            'R51': 'Cefalea',
            'D50.9': 'Anemia por deficiencia de hierro',
            'K29.7': 'Gastritis'
        }

        if archivo_csv and os.path.exists(archivo_csv):
            self.cargar_desde_csv(archivo_csv)

    def cargar_desde_csv(self, ruta_csv: str):
        """Carga mapeos adicionales desde un archivo CSV con separador ';'."""
        try:
            with open(ruta_csv, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                for fila in reader:
                    dx = fila.get('dx_local', '').strip().upper()
                    cie = fila.get('cie10', '').strip()
                    desc = fila.get('descripcion', '').strip()
                    if dx and cie:
                        self.mapeo_cie10[dx] = (cie, desc)
                        self.codigos_cie10_validos[cie] = desc
        except Exception as e:
            print(f"[Terminologia] Advertencia al cargar CSV: {e}")

    def mapear_diagnostico(self, dx_raw: str, descripcion_adicional: str = "") -> Optional[Tuple[str, str]]:
        """
        Mapea un diagnóstico local o código a su estándar CIE-10 (código, descripción).
        Retorna None si no existe equivalencia conocida.
        """
        if not dx_raw:
            return None

        clean = str(dx_raw).strip()
        upper = clean.upper()

        # 1. Búsqueda exacta en mapeos locales
        if upper in self.mapeo_cie10:
            return self.mapeo_cie10[upper]

        # 2. Si ya es un código CIE-10 estándar válido
        if clean in self.codigos_cie10_validos:
            desc = descripcion_adicional or self.codigos_cie10_validos[clean]
            return (clean, desc)

        # 3. Formato estándar CIE-10 (Letra seguida de 2 números y punto opcional)
        if len(clean) >= 3 and clean[0].isalpha() and clean[1:3].isdigit():
            desc = descripcion_adicional or f"Diagnóstico {clean}"
            return (clean, desc)

        return None

    def mapear_laboratorio(self, lab_raw: str) -> Optional[Tuple[str, str]]:
        """Mapea una prueba de laboratorio a LOINC."""
        if not lab_raw:
            return None
        upper = str(lab_raw).strip().upper()
        if upper in self.mapeo_loinc:
            return self.mapeo_loinc[upper]
        if '-' in lab_raw and any(c.isdigit() for c in lab_raw):
            return (lab_raw.strip(), f"Prueba {lab_raw}")
        return None

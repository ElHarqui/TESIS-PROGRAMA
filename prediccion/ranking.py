"""
Carga el ranking ponderado (CSV) y modela cada alumno con su ciclo estimado.

El ciclo NO viene en el ranking — se infiere del año de ingreso, que está codificado
en los dos primeros dígitos del código de alumno (ej: '22200033' → ingresó 2022).

Fórmula de inferencia:
    años_cursados = año_referencia - año_ingreso
    ciclos_completos = años_cursados * 2
    ciclo_actual = ciclos_completos + 1  (semestre en curso)

Asume avance regular (sin atrasados/adelantados). Es la aproximación más razonable
con los datos disponibles. Para precisión real se necesitaría matrícula por ciclo
de la facultad.
"""
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


# Año del ranking actualmente cargado. Si trabajamos con el ranking 2025-0 (=2025-I),
# las inferencias de ciclo se hacen RELATIVAS a ese semestre.
# Para predecir 2026-I a partir del ranking 2025-I se aplica un ajuste de +2 ciclos.
ANIO_REFERENCIA_DEFAULT = 2025


@dataclass(frozen=True)
class AlumnoRanking:
    """Una fila del ranking ponderado."""
    orden: int                 # 1 = primero en matricularse
    codigo: str                # ej. "22200033"
    ponderado: float           # ej. 14.402
    anio_ingreso: Optional[int]  # ej. 2022. None si el código no es estándar.
    ciclo_estimado: Optional[int]  # ej. 9. None si no se puede inferir.


def inferir_anio_ingreso(codigo: str) -> Optional[int]:
    """
    Extrae el año de ingreso del código de alumno UNMSM.

    Formato estándar: AANNNNNN (8 dígitos), donde AA = año de ingreso (2 últimos dígitos).
    Códigos viejos (formato distinto, ej. '973084') devuelven None.
    """
    if len(codigo) != 8 or not codigo.isdigit():
        return None
    yy = int(codigo[:2])
    # Heurística: ≤30 → 20yy, >30 → 19yy. Cubre alumnos 2000-2030 y casos viejos.
    return 2000 + yy if yy <= 30 else 1900 + yy


def inferir_ciclo_estimado(codigo: str, anio_referencia: int = ANIO_REFERENCIA_DEFAULT) -> Optional[int]:
    """
    Estima el ciclo en curso del alumno al `anio_referencia`.

    Asume avance regular: 2 ciclos por año desde el año de ingreso.
    Devuelve None si no se puede inferir el año de ingreso.

    Ejemplo: alumno ingresó 2022, referencia 2025 → 3 años × 2 = 6 ciclos completos,
    está cursando el ciclo 7.
    """
    anio = inferir_anio_ingreso(codigo)
    if anio is None:
        return None
    anios_cursados = anio_referencia - anio
    if anios_cursados < 0:
        return None
    ciclos_completos = anios_cursados * 2
    return ciclos_completos + 1


def cargar_ranking(
    path: str = "data/ranking_ponderado_2025_0.csv",
    anio_referencia: int = ANIO_REFERENCIA_DEFAULT,
) -> List[AlumnoRanking]:
    """
    Carga el CSV del ranking y enriquece cada fila con ciclo estimado.

    Si el archivo no existe, devuelve lista vacía (el sistema sigue funcionando
    sin módulo predictivo — `preferencia_cupos` cae al cálculo crudo).
    """
    p = Path(path)
    if not p.exists():
        return []

    alumnos = []
    with open(p, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            codigo = row["codigo_alumno"]
            alumnos.append(AlumnoRanking(
                orden=int(row["orden"]),
                codigo=codigo,
                ponderado=float(row["ponderado"]),
                anio_ingreso=inferir_anio_ingreso(codigo),
                ciclo_estimado=inferir_ciclo_estimado(codigo, anio_referencia),
            ))
    return alumnos

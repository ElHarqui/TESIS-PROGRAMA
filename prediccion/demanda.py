"""
Estimador de demanda de cupos basado en el ranking ponderado y la inferencia de ciclo.

Implementa la combinación de los Enfoques 1 + 3 discutidos en el diseño:

ENFOQUE 1 — Quién compite:
    Para una asignatura de ciclo C, los alumnos que VAN A COMPETIR por sus cupos son
    aquellos del ranking que (a) están estimados en el mismo ciclo C, y (b) tienen
    ponderado MAYOR al del alumno objetivo (por lo tanto se matriculan antes).

ENFOQUE 3 — Cómo se reparten (V1 determinista):
    Esos alumnos competidores se distribuyen entre las secciones de la asignatura
    de forma proporcional al `topeAlumnos` de cada sección (las secciones más grandes
    "atraen" más alumnos en proporción a su capacidad).

    V1 es determinista — no usa simulación Monte Carlo ni atractivo por horario/docente.
    Eso queda para V2.

PROYECCIÓN ENTRE SEMESTRES:
    Si el ranking es de un semestre anterior al que queremos predecir, se pasa
    `delta_ciclos`: la diferencia entre ambos semestres × 2 (un ciclo por semestre).
    Para predecir 2026-I usando ranking 2025-I → delta_ciclos = 2.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional

from models import Seccion
from data.parser import AsignaturaPlan
from .ranking import AlumnoRanking


@dataclass
class EstimadorDemanda:
    """
    Calcula un score 0-1 de "probabilidad de conseguir cupo" para cualquier sección.

    Score interpretado:
        1.0 → ningún alumno con mejor ponderado va a tomarla; cupo garantizado.
        0.0 → la demanda estimada supera o iguala la capacidad de la sección.

    Se construye una vez con todo el contexto y se consulta vía `score_cupo(seccion)`.
    Cachea por (codAsignatura, codSeccion) para no recalcular.
    """
    ranking: List[AlumnoRanking]
    ciclo_de_asignatura: Dict[str, int]            # codAsignatura → ciclo del plan
    secciones_por_asignatura: Dict[str, List[Seccion]]  # codAsignatura → todas sus secciones
    ponderado_objetivo: float
    delta_ciclos: int = 0                           # 0 si ranking es del mismo semestre

    def __post_init__(self):
        self._cache: Dict[tuple, float] = {}

    @classmethod
    def construir(
        cls,
        ranking: List[AlumnoRanking],
        plan: List[AsignaturaPlan],
        secciones_disponibles: List[Seccion],
        ponderado_objetivo: float,
        delta_ciclos: int = 0,
    ) -> "EstimadorDemanda":
        """Factory que pre-indexa plan y secciones."""
        ciclo_de_asignatura = {a.codAsignatura: a.ciclo for a in plan}
        secciones_por_asignatura: Dict[str, List[Seccion]] = {}
        for s in secciones_disponibles:
            secciones_por_asignatura.setdefault(s.codAsignatura, []).append(s)
        return cls(
            ranking=ranking,
            ciclo_de_asignatura=ciclo_de_asignatura,
            secciones_por_asignatura=secciones_por_asignatura,
            ponderado_objetivo=ponderado_objetivo,
            delta_ciclos=delta_ciclos,
        )

    def _alumnos_competidores(self, ciclo_asignatura: int) -> int:
        """
        Cantidad de alumnos del ranking que (a) cursan la asignatura en el semestre
        objetivo (ciclo_estimado + delta = ciclo_asignatura) y (b) tienen ponderado
        mayor al objetivo.
        """
        ciclo_efectivo_en_ranking = ciclo_asignatura - self.delta_ciclos
        return sum(
            1 for a in self.ranking
            if a.ciclo_estimado == ciclo_efectivo_en_ranking
            and a.ponderado > self.ponderado_objetivo
        )

    def score_cupo(self, seccion: Seccion) -> float:
        """
        Score 0-1 de probabilidad de conseguir cupo en esa sección.

        Si la asignatura no está en el plan (electivo no mapeado) o no se puede
        estimar, hace fallback a `seccion.disponibilidad / 100` (cálculo crudo).
        """
        key = (seccion.codAsignatura, seccion.codSeccion)
        if key in self._cache:
            return self._cache[key]

        ciclo_asig = self.ciclo_de_asignatura.get(seccion.codAsignatura)
        if ciclo_asig is None:
            score = seccion.disponibilidad / 100.0
            self._cache[key] = score
            return score

        compiten = self._alumnos_competidores(ciclo_asig)
        secs_misma_asig = self.secciones_por_asignatura.get(seccion.codAsignatura, [seccion])
        capacidad_total = sum(s.topeAlumnos for s in secs_misma_asig)

        if capacidad_total == 0:
            score = 0.0
        else:
            # Reparto proporcional al tope
            proporcion = seccion.topeAlumnos / capacidad_total
            demanda_estimada = compiten * proporcion
            cupo_libre = max(0.0, seccion.topeAlumnos - demanda_estimada)
            score = cupo_libre / seccion.topeAlumnos

        self._cache[key] = score
        return score

    def reporte_asignatura(self, cod_asignatura: str) -> Optional[Dict]:
        """
        Devuelve detalle del análisis para una asignatura (debug / diagnóstico).
        """
        ciclo = self.ciclo_de_asignatura.get(cod_asignatura)
        if ciclo is None:
            return None
        compiten = self._alumnos_competidores(ciclo)
        secs = self.secciones_por_asignatura.get(cod_asignatura, [])
        capacidad = sum(s.topeAlumnos for s in secs)
        return {
            "ciclo_asignatura": ciclo,
            "ciclo_en_ranking": ciclo - self.delta_ciclos,
            "alumnos_competidores": compiten,
            "n_secciones": len(secs),
            "capacidad_total": capacidad,
            "ratio_demanda_capacidad": compiten / capacidad if capacidad else None,
        }

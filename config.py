"""
Carga de configuración del sistema desde config_ga.json.

Externaliza los pesos del fitness y los parámetros del algoritmo genético para
poder tunearlos sin tocar código. Si el archivo no existe, se usan los defaults.
"""
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from fitness import PesosFitness


@dataclass
class ParametrosGA:
    """Parámetros del algoritmo genético, externalizables vía config_ga.json."""
    tamano_poblacion: int = 100
    generaciones: int = 50
    tasa_mutacion: float = 0.15
    tamano_torneo: int = 3
    elitismo: int = 5
    top_k: int = 5
    distancia_minima: int = 1
    seed: Optional[int] = 42


@dataclass
class ConfigPrediccion:
    """
    Configuración del módulo predictivo de vacantes (`prediccion/`).

    Cuando `activada=False` (default) el sistema NO usa el modulo predictivo:
    `preferencia_cupos` funciona con el calculo crudo de disponibilidad.

    Cuando se cambie a `True` (requiere implementar la integracion en
    `preferencia_cupos` y `main.py`), el resto de los campos parametrizan el
    modelo V1.5 documentado en `prediccion/README.md`.
    """
    activada: bool = False
    ranking_path: str = "data/ranking_ponderado_2025_0.csv"
    ranking_anio_referencia: int = 2025
    # Cuantos ciclos hay que sumar a un alumno del ranking para proyectarlo al
    # semestre objetivo. Ranking 2025-I -> 2026-I = +2 ciclos.
    semestre_target_delta_ciclos: int = 2
    # Para escalar la distribucion del ranking (3 escuelas) a la escuela del alumno.
    total_alumnos_escuela: int = 875        # Ing. Sistemas en 2026-I
    total_alumnos_ranking_origen: int = 1541  # alumnos del ranking 2025-0
    # Pesos de competencia por ciclo (V1.5 Opcion C).
    # El alumno cuenta con peso 1.0 para asignaturas de su ciclo nominal,
    # y peso 0.5 para asignaturas de ciclos vecinos (±1).
    peso_ciclo_nominal: float = 1.0
    peso_ciclo_vecino: float = 0.5


@dataclass
class Config:
    """Configuración completa del sistema."""
    pesos: PesosFitness = field(default_factory=PesosFitness)
    ga: ParametrosGA = field(default_factory=ParametrosGA)
    max_creditos: float = 24.0
    prediccion: ConfigPrediccion = field(default_factory=ConfigPrediccion)


def cargar_config(path: str = "config_ga.json") -> Config:
    """
    Carga la configuración desde JSON. Si el archivo no existe o le faltan campos,
    completa con los defaults de las dataclasses.

    Estructura esperada:
        {
          "fitness": {"peso_horarios": ..., "sub_peso_turno": ..., ...},
          "ga": {"tamano_poblacion": ..., "generaciones": ..., ...},
          "alumno": {"max_creditos": ...}
        }
    """
    p = Path(path)
    if not p.exists():
        return Config()

    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)

    fit = data.get("fitness", {})
    ga = data.get("ga", {})
    alu = data.get("alumno", {})
    pred = data.get("prediccion", {})

    defaults_pesos = PesosFitness()
    pesos = PesosFitness(
        peso_horarios=fit.get("peso_horarios", defaults_pesos.peso_horarios),
        peso_docentes=fit.get("peso_docentes", defaults_pesos.peso_docentes),
        peso_cupos=fit.get("peso_cupos", defaults_pesos.peso_cupos),
        sub_peso_turno=fit.get("sub_peso_turno", defaults_pesos.sub_peso_turno),
        sub_peso_dias_libres=fit.get("sub_peso_dias_libres", defaults_pesos.sub_peso_dias_libres),
        sub_peso_densidad=fit.get("sub_peso_densidad", defaults_pesos.sub_peso_densidad),
    )

    defaults_ga = ParametrosGA()
    parametros = ParametrosGA(
        tamano_poblacion=ga.get("tamano_poblacion", defaults_ga.tamano_poblacion),
        generaciones=ga.get("generaciones", defaults_ga.generaciones),
        tasa_mutacion=ga.get("tasa_mutacion", defaults_ga.tasa_mutacion),
        tamano_torneo=ga.get("tamano_torneo", defaults_ga.tamano_torneo),
        elitismo=ga.get("elitismo", defaults_ga.elitismo),
        top_k=ga.get("top_k", defaults_ga.top_k),
        distancia_minima=ga.get("distancia_minima", defaults_ga.distancia_minima),
        seed=ga.get("seed", defaults_ga.seed),
    )

    defaults_pred = ConfigPrediccion()
    prediccion_cfg = ConfigPrediccion(
        activada=pred.get("activada", defaults_pred.activada),
        ranking_path=pred.get("ranking_path", defaults_pred.ranking_path),
        ranking_anio_referencia=pred.get("ranking_anio_referencia", defaults_pred.ranking_anio_referencia),
        semestre_target_delta_ciclos=pred.get("semestre_target_delta_ciclos", defaults_pred.semestre_target_delta_ciclos),
        total_alumnos_escuela=pred.get("total_alumnos_escuela", defaults_pred.total_alumnos_escuela),
        total_alumnos_ranking_origen=pred.get("total_alumnos_ranking_origen", defaults_pred.total_alumnos_ranking_origen),
        peso_ciclo_nominal=pred.get("peso_ciclo_nominal", defaults_pred.peso_ciclo_nominal),
        peso_ciclo_vecino=pred.get("peso_ciclo_vecino", defaults_pred.peso_ciclo_vecino),
    )

    return Config(
        pesos=pesos,
        ga=parametros,
        max_creditos=alu.get("max_creditos", 24.0),
        prediccion=prediccion_cfg,
    )

import json
from pathlib import Path
from typing import Dict

from .contexto import PreferenciasHorario


SCORE_NEUTRAL = 0.5


def cargar_scores_docentes(path: str = "data/preferencias_docentes.json") -> Dict[str, float]:
    """
    Carga scores manuales de docentes desde JSON. Si el archivo no existe o no tiene
    'scores', retorna dict vacío (todo docente será tratado como neutral=0.5 en evaluación).

    Formato esperado:
        {"scores": {"codDocente": 0.8, ...}}

    Convención de scores:
        0.0 = evitar a toda costa
        0.5 = neutral (default)
        1.0 = preferencia máxima
    """
    p = Path(path)
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("scores", {})


def cargar_preferencias_horarios(path: str = "data/preferencias_horarios.json") -> PreferenciasHorario:
    """
    Carga preferencias de horario desde JSON. Si el archivo no existe o no tiene los
    campos, devuelve un PreferenciasHorario con defaults "indiferente" (todos los
    sub-scores caen a neutral 0.5).

    Formato esperado:
        {
          "turno_preferido": "manana"|"tarde"|"noche"|"indiferente",
          "dias_libres_deseados": ["SABADO", "DOMINGO"],
          "densidad": "compacto"|"distribuido"|"indiferente"
        }
    """
    p = Path(path)
    if not p.exists():
        return PreferenciasHorario()
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    return PreferenciasHorario(
        turno_preferido=data.get("turno_preferido", "indiferente"),
        dias_libres_deseados=[d.upper() for d in data.get("dias_libres_deseados", [])],
        densidad=data.get("densidad", "indiferente"),
    )

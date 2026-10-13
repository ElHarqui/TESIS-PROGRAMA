import json
from pathlib import Path
from typing import Dict, Optional

from data.cache import sanitizar_usuario
from .contexto import PreferenciasHorario


SCORE_NEUTRAL = 0.5


def resolver_ruta_preferencias(
    tipo: str,
    usuario_o_path: Optional[str] = None,
    *,
    usuario: Optional[str] = None,
    path: Optional[str] = None,
) -> Path:
    """
    Resuelve la ruta física del archivo de preferencias ('docentes' o 'horarios').
    - Si se especifica un path explícito, se usa directamente.
    - Si se especifica un usuario (por argumento o inferido de usuario_o_path),
      se aísla en data/users/{usuario}/preferencias_{tipo}.json.
    - En caso contrario, se usa la ruta por defecto data/preferencias_{tipo}.json.
    """
    final_path = path
    final_user = usuario

    if usuario_o_path is not None:
        if usuario_o_path.endswith(".json") or "/" in usuario_o_path or "\\" in usuario_o_path:
            final_path = usuario_o_path
        else:
            final_user = usuario_o_path

    if final_path:
        return Path(final_path)

    u_limpio = sanitizar_usuario(final_user)
    if u_limpio:
        return Path("data/users") / u_limpio / f"preferencias_{tipo}.json"

    return Path(f"data/preferencias_{tipo}.json")


def cargar_scores_docentes(
    usuario_o_path: Optional[str] = None,
    *,
    usuario: Optional[str] = None,
    path: Optional[str] = None,
) -> Dict[str, float]:
    """
    Carga scores manuales de docentes desde JSON. Si el archivo no existe o no tiene
    'scores', retorna dict vacío (todo docente será tratado como neutral=0.5 en evaluación).

    Formato esperado:
        {"scores": {"codDocente": 0.8, ...}}
    """
    p = resolver_ruta_preferencias("docentes", usuario_o_path, usuario=usuario, path=path)
    if not p.exists():
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("scores", {})
    except (json.JSONDecodeError, OSError):
        return {}


def guardar_scores_docentes(
    scores: Dict[str, float],
    usuario_o_path: Optional[str] = None,
    *,
    usuario: Optional[str] = None,
    path: Optional[str] = None,
) -> Path:
    """
    Guarda los scores de docentes en el JSON correspondiente al usuario o ruta especificada.
    """
    p = resolver_ruta_preferencias("docentes", usuario_o_path, usuario=usuario, path=path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"scores": scores}, f, ensure_ascii=False, indent=2)
    return p


def cargar_preferencias_horarios(
    usuario_o_path: Optional[str] = None,
    *,
    usuario: Optional[str] = None,
    path: Optional[str] = None,
) -> PreferenciasHorario:
    """
    Carga preferencias de horario desde JSON. Si el archivo no existe o no tiene los
    campos, devuelve un PreferenciasHorario con defaults (SOFT en "indiferente",
    HARD sin restricción).
    """
    p = resolver_ruta_preferencias("horarios", usuario_o_path, usuario=usuario, path=path)
    if not p.exists():
        return PreferenciasHorario()
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return PreferenciasHorario()

    return PreferenciasHorario(
        turno_preferido=data.get("turno_preferido", "indiferente"),
        dias_libres_deseados=[d.upper() for d in data.get("dias_libres_deseados", [])],
        densidad=data.get("densidad", "indiferente"),
        dias_libres_obligatorios=[d.upper() for d in data.get("dias_libres_obligatorios", [])],
        hora_min=data.get("hora_min") or None,
        hora_max=data.get("hora_max") or None,
    )


def guardar_preferencias_horarios(
    prefs: PreferenciasHorario,
    usuario_o_path: Optional[str] = None,
    *,
    usuario: Optional[str] = None,
    path: Optional[str] = None,
) -> Path:
    """
    Guarda las preferencias de horario en el JSON correspondiente al usuario o ruta especificada.
    """
    p = resolver_ruta_preferencias("horarios", usuario_o_path, usuario=usuario, path=path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "turno_preferido": prefs.turno_preferido,
        "dias_libres_deseados": prefs.dias_libres_deseados,
        "densidad": prefs.densidad,
        "dias_libres_obligatorios": prefs.dias_libres_obligatorios,
        "hora_min": prefs.hora_min,
        "hora_max": prefs.hora_max,
    }
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return p


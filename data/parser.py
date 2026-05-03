from typing import List, Set
from dataclasses import dataclass, field
from models import BloqueHorario, Seccion


# ──────────────────────────────────────────────
# MODELOS NUEVOS (datos del alumno y plan)
# ──────────────────────────────────────────────

@dataclass
class DatosAlumno:
    numDocumento: str = ""
    correoInstitucional: str = ""
    correoPersonal: str = ""
    celular: str = ""
    anioIngreso: str = ""
    codFacultad: int = 0
    codEscuela: int = 0
    codPlan: str = ""
    cicloActual: int = 0
    creditosAprobados: float = 0.0
    promedioPonderado: float = 0.0
    raw: dict = field(default_factory=dict)


@dataclass
class AsignaturaPlan:
    ciclo: int
    codAsignatura: str
    desAsignatura: str
    creditos: float
    tipoAsignatura: str        # "E" = electivo, "O" = obligatorio, etc.
    codAsignaturaPre: str      # "NR" = sin prerequisito
    desAsignaturaPre: str
    creditosPre: float
    codPlan: str = ""          


# ──────────────────────────────────────────────
# PARSERS
# ──────────────────────────────────────────────

def parsear_seccion(raw: dict) -> Seccion:
    bloques = [
        BloqueHorario(
            codAsignatura=h["codAsignatura"],
            codSeccion=h["codSeccion"],
            codDocente=h["codDocente"],
            horario=h["horario"],
            dia=h["dia"],
            horaInicio=h["horaInicio"],
            horaFin=h["horaFin"],
            codAula=h["codAula"],
            tipo=h["codTipoHoraAsignatura"],
            desTipo=h["desTipoHoraAsignatura"],
        )
        for h in raw.get("horarios", [])
    ]
    return Seccion(
        ciclo=raw["ciclo"],
        codAsignatura=raw["codAsignatura"],
        desAsignatura=raw["desAsignatura"],
        creditos=raw["creditos"],
        codSeccion=raw["codSeccion"],
        codDocente=raw["codDocente"],
        nomDocente=raw["nomDocente"],
        apePatDocente=raw["apePatDocente"],
        apeMatDocente=raw["apeMatDocente"],
        topeAlumnos=raw["topeAlumnos"],
        matriculados=raw["matriculados"],
        bloques=bloques,
    )


def parsear_respuesta(data) -> List[Seccion]:
    """Parsea el JSON de programacion → lista de Seccion."""
    secciones_raw = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(secciones_raw, dict):
        for key in secciones_raw:
            if isinstance(secciones_raw[key], list):
                secciones_raw = secciones_raw[key]
                break
    return [parsear_seccion(s) for s in secciones_raw]


def parsear_alumno(data: dict) -> DatosAlumno:
    """Parsea el JSON de /informacion/perfil → DatosAlumno."""
    raw = data.get("data", data) if isinstance(data, dict) else data
    return DatosAlumno(
        numDocumento=raw.get("numDocumento", ""),
        correoInstitucional=raw.get("correoInstitucional", ""),
        correoPersonal=raw.get("correoPersonal", ""),
        celular=raw.get("celular", ""),
        anioIngreso=raw.get("anioIngreso", ""),
        codFacultad=int(raw.get("codFacultad", 0)),
        codEscuela=int(raw.get("codEscuela", 0)),
        codPlan=raw.get("codPlan", "").strip(),
        cicloActual=int(raw.get("anioEstudio", 0)),        # ← corregido
        creditosAprobados=float(raw.get("creditosAprobados", 0.0)),
        promedioPonderado=float(raw.get("promedio", 0.0)), # ← corregido
        raw=raw,
    )


def parsear_plan_estudios(data: dict) -> List[AsignaturaPlan]:
    """
    Parsea el JSON de /planEstudios → lista de AsignaturaPlan.
    Cada item incluye su prerequisito en codAsignaturaPre
    ('NR' significa sin prerequisito).
    """
    raw_list = data.get("data", data) if isinstance(data, dict) else data
    result = []
    for item in raw_list:
        result.append(AsignaturaPlan(
            ciclo=item.get("ciclo", 0),
            codAsignatura=item.get("codAsignatura", ""),
            desAsignatura=item.get("desAsignatura", "").strip(),
            creditos=float(item.get("creditos", 0.0)),
            tipoAsignatura=item.get("tipoAsignatura", ""),
            codAsignaturaPre=item.get("codAsignaturaPre", "NR"),
            desAsignaturaPre=item.get("desAsignaturaPre", "NR"),
            creditosPre=float(item.get("creditosPre", 0.0)),
        ))
    return result


def extraer_prerequisitos(plan: List[AsignaturaPlan]) -> dict:
    """
    A partir del plan de estudios, construye un dict:
        { codAsignatura → codAsignaturaPre | None }

    'NR' y '--' se tratan como sin prerequisito (None).
    Útil para hard_constraints.verificar_prerequisitos().
    """
    SIN_PRE = {"NR", "--", "", None}
    return {
        a.codAsignatura: (None if a.codAsignaturaPre in SIN_PRE else a.codAsignaturaPre)
        for a in plan
    }


def parsear_prematricula(data: dict) -> list:
    """
    Parsea el JSON de /reportes/prematricula → lista cruda de asignaturas
    en prematrícula. Se guarda como lista de dicts para el módulo predictivo.
    """
    raw_list = data.get("data", data) if isinstance(data, dict) else data
    return raw_list if isinstance(raw_list, list) else []
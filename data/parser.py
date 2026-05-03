from typing import List
from models import BloqueHorario, Seccion


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
    secciones_raw = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(secciones_raw, dict):
        for key in secciones_raw:
            if isinstance(secciones_raw[key], list):
                secciones_raw = secciones_raw[key]
                break
    return [parsear_seccion(s) for s in secciones_raw]
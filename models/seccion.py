from dataclasses import dataclass, field
from typing import List
from .bloque import BloqueHorario


@dataclass
class Seccion:
    ciclo: int
    codAsignatura: str
    desAsignatura: str
    creditos: float
    codSeccion: int
    codDocente: str
    nomDocente: str
    apePatDocente: str
    apeMatDocente: str
    topeAlumnos: int
    matriculados: int
    bloques: List[BloqueHorario] = field(default_factory=list)

    @property
    def docente_completo(self) -> str:
        return f"{self.apePatDocente} {self.apeMatDocente}, {self.nomDocente}"

    @property
    def disponibilidad(self) -> float:
        if self.topeAlumnos == 0:
            return 0.0
        return (self.topeAlumnos - self.matriculados) / self.topeAlumnos * 100
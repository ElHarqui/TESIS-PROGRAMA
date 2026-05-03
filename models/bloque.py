from dataclasses import dataclass


@dataclass
class BloqueHorario:
    codAsignatura: str
    codSeccion: int
    codDocente: str
    horario: int
    dia: str
    horaInicio: str
    horaFin: str
    codAula: str
    tipo: str
    desTipo: str

    @property
    def hora_inicio_int(self) -> int:
        h, m = map(int, self.horaInicio.split(":"))
        return h * 60 + m

    @property
    def hora_fin_int(self) -> int:
        h, m = map(int, self.horaFin.split(":"))
        return h * 60 + m

    def choca_con(self, otro: "BloqueHorario") -> bool:
        if self.dia != otro.dia:
            return False
        return self.hora_inicio_int < otro.hora_fin_int and otro.hora_inicio_int < self.hora_fin_int
    from dataclasses import dataclass, field
    from typing import List, Optional

    # --- MODELOS DE DATOS ---

    @dataclass
    class BloqueHorario:
        codAsignatura: str
        codSeccion: int
        codDocente: str
        horario: int          # índice del bloque (1, 2, ...)
        dia: str              # "LUNES", "MARTES", etc.
        horaInicio: str       # "18:00"
        horaFin: str          # "20:00"
        codAula: str          # "--" si no asignada
        tipo: str             # "T" = Teoría, "P" = Práctica, "L" = Lab
        desTipo: str          # "Teoría", "Práctica"

        @property
        def hora_inicio_int(self) -> int:
            """Convierte '18:00' a 1080 (minutos desde medianoche) — útil para comparar choques"""
            h, m = map(int, self.horaInicio.split(":"))
            return h * 60 + m

        @property
        def hora_fin_int(self) -> int:
            h, m = map(int, self.horaFin.split(":"))
            return h * 60 + m

        def choca_con(self, otro: "BloqueHorario") -> bool:
            """True si dos bloques se solapan en día y hora"""
            if self.dia != otro.dia:
                return False
            return self.hora_inicio_int < otro.hora_fin_int and otro.hora_inicio_int < self.hora_fin_int


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
            """Porcentaje de cupos disponibles"""
            if self.topeAlumnos == 0:
                return 0.0
            return (self.topeAlumnos - self.matriculados) / self.topeAlumnos * 100


    # --- PARSER ---

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

    def parsear_respuesta(data: dict) -> List[Seccion]:
        """Parsea el JSON completo del endpoint"""
        secciones_raw = data.get("data", data) if isinstance(data, dict) else data
        if isinstance(secciones_raw, dict):
            # a veces viene envuelto en otra clave, ajusta según tu respuesta real
            for key in secciones_raw:
                if isinstance(secciones_raw[key], list):
                    secciones_raw = secciones_raw[key]
                    break
        return [parsear_seccion(s) for s in secciones_raw]


    # --- USO COMPLETO ---

    import requests, json

    cookies = {
        "JSESSIONID": "1DA424482E11CB22B8FD5F1C250E7CBB",
        "2e4302301d994214b74f1c6e9c6e2763": "WyIxNTg0NjA1ODA5Il0",
        "_ga": "GA1.1.2092739237.1721236380",
        "HWWAFSESID": "08d877303822411e75",
        "HWWAFSESTIME": "1777513278205",
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://sum.unmsm.edu.pe/alumnoWebSum/v2/matricula/programacion",
        "X-Requested-With": "AlumnoWebSum2026Q1",
        "Accept": "*/*",
    }

    url = "https://sum.unmsm.edu.pe/alumnoWebSum/v2/matricula/programacion"
    params = {"accion": "obtenerProgramacionAsignaturas"}

    response = requests.get(url, cookies=cookies, headers=headers, params=params)
    data = response.json()

    secciones = parsear_respuesta(data)

    # Ejemplo: ver todas las secciones
    for s in secciones:
        print(f"\n[Ciclo {s.ciclo}] {s.desAsignatura} - Sección {s.codSeccion}")
        print(f"  Docente: {s.docente_completo}")
        print(f"  Cupos: {s.matriculados}/{s.topeAlumnos} ({s.disponibilidad:.0f}% libre)")
        for b in s.bloques:
            print(f"  {b.dia} {b.horaInicio}-{b.horaFin} [{b.desTipo}] Aula: {b.codAula}")
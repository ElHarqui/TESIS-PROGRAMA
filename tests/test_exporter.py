import os
from pathlib import Path
import pytest
from models import BloqueHorario, Seccion, Cromosoma, HorarioResultado
from output.exporter import exportar_excel, exportar_pdf


def _crear_seccion(cod: str) -> Seccion:
    b = BloqueHorario(
        codAsignatura=cod,
        codSeccion=1,
        codDocente="DOC1",
        horario=1,
        dia="LUNES",
        horaInicio="08:00",
        horaFin="10:00",
        codAula="A101",
        tipo="T",
        desTipo="TEORIA",
    )
    return Seccion(
        ciclo=7,
        codAsignatura=cod,
        desAsignatura=f"CURSO {cod}",
        creditos=4.0,
        codSeccion=1,
        codDocente="DOC1",
        nomDocente="JUAN",
        apePatDocente="PEREZ",
        apeMatDocente="GARCIA",
        topeAlumnos=40,
        matriculados=20,
        bloques=[b],
    )


class TestExporter:
    def test_exportar_excel_con_horario_resultado(self, tmp_path):
        c = Cromosoma([_crear_seccion("C1")])
        h_res = HorarioResultado(
            rank=1,
            cromosoma=c,
            fitness=0.85,
            score_horarios=0.9,
            score_docentes=0.8,
            score_cupos=0.85,
            creditos=4.0,
        )
        out_file = tmp_path / "test_horarios.xlsx"
        res_path = exportar_excel([h_res], filename=str(out_file))

        assert res_path.exists()
        assert res_path.stat().st_size > 0

    def test_exportar_pdf_con_horario_resultado(self, tmp_path):
        c = Cromosoma([_crear_seccion("C1")])
        h_res = HorarioResultado(
            rank=1,
            cromosoma=c,
            fitness=0.85,
            score_horarios=0.9,
            score_docentes=0.8,
            score_cupos=0.85,
            creditos=4.0,
        )
        out_file = tmp_path / "test_horarios.pdf"
        res_path = exportar_pdf([h_res], filename=str(out_file))

        assert res_path.exists()
        assert res_path.stat().st_size > 0

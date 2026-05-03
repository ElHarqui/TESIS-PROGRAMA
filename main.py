import asyncio
import os
from dotenv import load_dotenv
from data import obtener_datos_sum, parsear_respuesta

load_dotenv()


async def main():
    usuario = os.getenv("LOGIN")
    password = os.getenv("PASSWORD")

    if not usuario or not password:
        raise EnvironmentError("Faltan las variables LOGIN o PASSWORD en .env")

    data = await obtener_datos_sum(usuario, password)
    secciones = parsear_respuesta(data)
    print(f"\n📚 Total secciones encontradas: {len(secciones)}\n")

    for s in secciones:
        print(f"[Ciclo {s.ciclo}] {s.desAsignatura} - Sección {s.codSeccion}")
        print(f"  Docente: {s.docente_completo}")
        print(f"  Cupos: {s.matriculados}/{s.topeAlumnos} ({s.disponibilidad:.0f}% libre)")
        for b in s.bloques:
            print(f"  {b.dia} {b.horaInicio}-{b.horaFin} [{b.desTipo}] Aula: {b.codAula}")
        print()

if __name__ == "__main__":
    asyncio.run(main())
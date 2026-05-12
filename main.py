import asyncio
import os
from dotenv import load_dotenv
from data import (
    obtener_datos_sum,
    parsear_respuesta,
    parsear_alumno,
    parsear_plan_estudios,
    extraer_prerequisitos,
    parsear_prematricula,
    Cache,
    parsear_historial,
    extraer_aprobados,
)

load_dotenv()

CACHE_KEY = "datos_sum"


async def main():
    usuario  = os.getenv("LOGIN")
    password = os.getenv("PASSWORD")

    if not usuario or not password:
        raise EnvironmentError("Faltan las variables LOGIN o PASSWORD en .env")

    # ── 1. Caché ──────────────────────────────────────────────
    cache = Cache(ttl=3600)  # 1 hora
    cache.limpiar_expirados()

    datos_raw = cache.get(CACHE_KEY)
    if datos_raw:
        print("⚡ Datos cargados desde caché (sin scraping)\n")
    else:
        print("🌐 Caché vacío o expirado — iniciando scraping...\n")
        datos_raw = await obtener_datos_sum(usuario, password)
        cache.set(CACHE_KEY, datos_raw)
        print("💾 Datos guardados en caché\n")

    # ── 2. Parsing ────────────────────────────────────────────
    secciones     = parsear_respuesta(datos_raw["programacion"])
    alumno        = parsear_alumno(datos_raw["alumno"])
    plan          = parsear_plan_estudios(datos_raw["plan_estudios"])
    prerequisitos = extraer_prerequisitos(plan)
    prematricula  = parsear_prematricula(datos_raw["prematricula"])
    historial  = parsear_historial(datos_raw["historial"])
    aprobados  = extraer_aprobados(historial)

    # ── 3. Resumen alumno ─────────────────────────────────────
    cod_plan = plan[0].codPlan if plan else "N/A"
    print(f"\n{'='*55}")
    print(f"👤 DNI:            {alumno.numDocumento}")
    print(f"📧 Correo:         {alumno.correoInstitucional}")
    print(f"📅 Ingreso:        {alumno.anioIngreso}")
    print(f"📊 Ciclo actual:   {alumno.cicloActual}")
    print(f"⭐ Promedio:       {alumno.promedioPonderado}")
    print(f"📋 Plan:           {cod_plan}")
    print(f"📌 Sit. académica: {alumno.raw.get('situAcademica', '')}")
    print(f"{'='*55}\n")

    # ── 4. Plan de estudios ───────────────────────────────────
    print(f"📖 Plan de estudios: {len(plan)} asignaturas")
    asig_con_pre = {k: v for k, v in prerequisitos.items() if v is not None}
    print(f"🔗 Con prerequisito: {len(asig_con_pre)}")
    print(f"✅ Sin prerequisito: {len(prerequisitos) - len(asig_con_pre)}\n")

    # ── 5. Prematrícula ───────────────────────────────────────
    print(f"📝 Asignaturas en prematrícula: {len(prematricula)}")
    for p in prematricula:
        print(f"   - {p.get('desAsignatura', '')} ({p.get('codAsignatura', '')})")
    print()

    # ── 6. Secciones disponibles ──────────────────────────────
    print(f"📚 Secciones disponibles: {len(secciones)}\n")
    for s in secciones:
        print(f"[Ciclo {s.ciclo}] {s.desAsignatura} - Sección {s.codSeccion}")
        print(f"  Docente: {s.docente_completo}")
        print(f"  Cupos:   {s.matriculados}/{s.topeAlumnos} ({s.disponibilidad:.0f}% libre)")
        for b in s.bloques:
            print(f"  {b.dia:10} {b.horaInicio}-{b.horaFin}  [{b.desTipo}]  Aula: {b.codAula}")
        print()
        
    # ── 7. Historial académico ─────────────────────────────────
    print(f"📜 Historial académico: {len(historial)} registros")
    print(f"✅ Asignaturas aprobadas: {len(aprobados)}")
    print(f"📊 Promedio histórico: {sum(r.calificacion for r in historial) / len(historial):.1f}\n")
    # ── 8. Endpoints fallidos ─────────────────────────────────
    if datos_raw.get("errores"):
        print(f"⚠️  Endpoints fallidos: {datos_raw['errores']}")


if __name__ == "__main__":
    asyncio.run(main())
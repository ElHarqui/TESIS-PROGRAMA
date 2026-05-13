import asyncio
import os
import time

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
from fitness import (
    ContextoAlumno,
    cargar_scores_docentes,
    cargar_preferencias_horarios,
    evaluar_fitness,
    preferencia_docentes,
    preferencia_cupos,
    preferencia_horarios,
)
from genetic import generar_poblacion_inicial, ejecutar_ga, top_k_diversos
from genetic.population import _es_seccion_valida

load_dotenv()

CACHE_KEY = "datos_sum"

# ──────────────────────────────────────────────
# CONFIGURACIÓN DEL GA (tunear si hace falta)
# ──────────────────────────────────────────────
GA_TAMANO_POBLACION = 100
GA_GENERACIONES     = 50
GA_TASA_MUTACION    = 0.15
GA_TAMANO_TORNEO    = 3
GA_ELITISMO         = 5
GA_TOP_K            = 5
GA_DISTANCIA_MINIMA = 1
GA_SEED             = 42  # None para no determinístico

# Orden canónico de días para mostrar el horario
ORDEN_DIAS = ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"]


def _imprimir_horario(rank: int, cromosoma, ctx: ContextoAlumno):
    fit = evaluar_fitness(cromosoma, ctx)
    p_hor = preferencia_horarios(cromosoma, ctx)
    p_doc = preferencia_docentes(cromosoma, ctx)
    p_cup = preferencia_cupos(cromosoma, ctx)
    creditos = sum(s.creditos for s in cromosoma.secciones)

    print(f"\n{'═' * 75}")
    print(f"HORARIO #{rank}   fitness={fit:.4f}   horarios={p_hor:.2f}   docentes={p_doc:.2f}   cupos={p_cup:.2f}   créditos={creditos:.0f}")
    print(f"{'═' * 75}")

    # Aplanar bloques con info de su sección, ordenar por día y hora
    eventos = []
    for s in cromosoma.secciones:
        for b in s.bloques:
            eventos.append((b, s))
    eventos.sort(key=lambda e: (ORDEN_DIAS.index(e[0].dia) if e[0].dia in ORDEN_DIAS else 99, e[0].horaInicio))

    dia_actual = None
    for b, s in eventos:
        prefijo_dia = b.dia if b.dia != dia_actual else " " * len(b.dia)
        dia_actual = b.dia
        cupo = f"{s.matriculados}/{s.topeAlumnos}"
        print(f"  {prefijo_dia:9} {b.horaInicio}-{b.horaFin}  {s.desAsignatura.strip()[:34]:34}  Sec{s.codSeccion}  cupo={cupo:>6}  [{b.desTipo}]")
        if b is s.bloques[0]:
            print(f"  {' '*9}              Docente: {s.docente_completo}")


async def main():
    usuario  = os.getenv("LOGIN")
    password = os.getenv("PASSWORD")

    if not usuario or not password:
        raise EnvironmentError("Faltan las variables LOGIN o PASSWORD en .env")

    # ── 1. Caché ──────────────────────────────────────────────
    cache = Cache(ttl=3600)
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
    historial     = parsear_historial(datos_raw["historial"])
    aprobados     = extraer_aprobados(historial)

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

    print(f"📖 Plan: {len(plan)} asignaturas  |  📝 Prematrícula: {len(prematricula)}  |  📚 Secciones: {len(secciones)}  |  ✅ Aprobadas: {len(aprobados)}\n")

    # ── 4. Construir contexto del alumno ──────────────────────
    contexto = ContextoAlumno(
        prerequisitos=prerequisitos,
        aprobados=aprobados,
        max_creditos=24.0,
        scores_docentes=cargar_scores_docentes(),
        prefs_horario=cargar_preferencias_horarios(),
    )

    # ── 5. Preparar input del GA ──────────────────────────────
    asignaturas_objetivo = [p["codAsignatura"] for p in prematricula]
    secciones_por_asig = {}
    for s in secciones:
        if _es_seccion_valida(s):
            secciones_por_asig.setdefault(s.codAsignatura, []).append(s)

    # ── 6. Población inicial ──────────────────────────────────
    print(f"🧬 Generando población inicial ({GA_TAMANO_POBLACION} cromosomas)...")
    poblacion, omitidas = generar_poblacion_inicial(
        asignaturas_objetivo,
        secciones,
        tamano_poblacion=GA_TAMANO_POBLACION,
        seed=GA_SEED,
    )

    if omitidas:
        print(f"⚠️  Asignaturas SIN sección disponible (omitidas del horario):")
        for cod in omitidas:
            desc = next((p["desAsignatura"].strip() for p in prematricula if p["codAsignatura"] == cod), "?")
            print(f"     {cod} — {desc}")
        print()

    fitness_ini = [evaluar_fitness(c, contexto) for c in poblacion]
    n_val_ini = sum(1 for f in fitness_ini if f > 0)
    print(f"  Gen 0:  válidos={n_val_ini}/{GA_TAMANO_POBLACION}  best={max(fitness_ini):.4f}  avg={sum(fitness_ini)/len(fitness_ini):.4f}")

    # ── 7. Ejecutar GA ────────────────────────────────────────
    print(f"🔬 Ejecutando GA por {GA_GENERACIONES} generaciones...")
    t0 = time.time()
    evaluador = lambda c: evaluar_fitness(c, contexto)
    poblacion_final = ejecutar_ga(
        poblacion,
        evaluador=evaluador,
        secciones_por_asig=secciones_por_asig,
        max_generaciones=GA_GENERACIONES,
        tasa_mutacion=GA_TASA_MUTACION,
        tamano_torneo=GA_TAMANO_TORNEO,
        elitismo=GA_ELITISMO,
    )
    duracion = time.time() - t0

    fitness_fin = [evaluar_fitness(c, contexto) for c in poblacion_final]
    n_val_fin = sum(1 for f in fitness_fin if f > 0)
    print(f"  Gen {GA_GENERACIONES}: válidos={n_val_fin}/{GA_TAMANO_POBLACION}  best={max(fitness_fin):.4f}  avg={sum(fitness_fin)/len(fitness_fin):.4f}  ({duracion:.2f}s)\n")

    # ── 8. Top-K diversos ─────────────────────────────────────
    top = top_k_diversos(poblacion_final, fitness_fin, k=GA_TOP_K, distancia_minima=GA_DISTANCIA_MINIMA)

    if not top:
        print("❌ El GA no encontró ningún horario válido.")
        print("   Probables causas: choques inevitables o créditos excedidos.")
        return

    print(f"\n🎯 Top-{len(top)} horarios diversos:")
    for rank, c in enumerate(top, 1):
        _imprimir_horario(rank, c, contexto)

    if len(top) < GA_TOP_K:
        print(f"\nℹ️  Solo se encontraron {len(top)} horarios suficientemente diversos (pedidos {GA_TOP_K}).")

    # ── 9. Endpoints fallidos ─────────────────────────────────
    if datos_raw.get("errores"):
        print(f"\n⚠️  Endpoints fallidos: {datos_raw['errores']}")


if __name__ == "__main__":
    asyncio.run(main())

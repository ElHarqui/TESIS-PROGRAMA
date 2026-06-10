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
from output import visualizar_grilla, leyenda_asignaturas, exportar_excel, exportar_pdf
from config import cargar_config

load_dotenv()

CACHE_KEY = "datos_sum"

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
    print(visualizar_grilla(cromosoma))
    print()
    print("Leyenda:")
    print(leyenda_asignaturas(cromosoma))


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
    config = cargar_config()
    contexto = ContextoAlumno(
        prerequisitos=prerequisitos,
        aprobados=aprobados,
        max_creditos=config.max_creditos,
        scores_docentes=cargar_scores_docentes(),
        prefs_horario=cargar_preferencias_horarios(),
        pesos=config.pesos,
    )

    # ── 5. Preparar input del GA ──────────────────────────────
    ga = config.ga
    asignaturas_objetivo = [p["codAsignatura"] for p in prematricula]
    secciones_por_asig = {}
    for s in secciones:
        if _es_seccion_valida(s):
            secciones_por_asig.setdefault(s.codAsignatura, []).append(s)

    # ── 6. Población inicial ──────────────────────────────────
    print(f"🧬 Generando población inicial ({ga.tamano_poblacion} cromosomas)...")
    poblacion, omitidas = generar_poblacion_inicial(
        asignaturas_objetivo,
        secciones,
        tamano_poblacion=ga.tamano_poblacion,
        seed=ga.seed,
    )

    if omitidas:
        print(f"⚠️  Asignaturas SIN sección disponible (omitidas del horario):")
        for cod in omitidas:
            desc = next((p["desAsignatura"].strip() for p in prematricula if p["codAsignatura"] == cod), "?")
            print(f"     {cod} — {desc}")
        print()

    fitness_ini = [evaluar_fitness(c, contexto) for c in poblacion]
    n_val_ini = sum(1 for f in fitness_ini if f > 0)
    print(f"  Gen 0:  válidos={n_val_ini}/{ga.tamano_poblacion}  best={max(fitness_ini):.4f}  avg={sum(fitness_ini)/len(fitness_ini):.4f}")

    # ── 7. Ejecutar GA ────────────────────────────────────────
    print(f"🔬 Ejecutando GA por {ga.generaciones} generaciones...")
    t0 = time.time()
    evaluador = lambda c: evaluar_fitness(c, contexto)
    poblacion_final = ejecutar_ga(
        poblacion,
        evaluador=evaluador,
        secciones_por_asig=secciones_por_asig,
        max_generaciones=ga.generaciones,
        tasa_mutacion=ga.tasa_mutacion,
        tamano_torneo=ga.tamano_torneo,
        elitismo=ga.elitismo,
    )
    duracion = time.time() - t0

    fitness_fin = [evaluar_fitness(c, contexto) for c in poblacion_final]
    n_val_fin = sum(1 for f in fitness_fin if f > 0)
    print(f"  Gen {ga.generaciones}: válidos={n_val_fin}/{ga.tamano_poblacion}  best={max(fitness_fin):.4f}  avg={sum(fitness_fin)/len(fitness_fin):.4f}  ({duracion:.2f}s)\n")

    # ── 8. Top-K diversos ─────────────────────────────────────
    top = top_k_diversos(poblacion_final, fitness_fin, k=ga.top_k, distancia_minima=ga.distancia_minima)

    if not top:
        print("❌ El GA no encontró ningún horario válido.")
        print("   Probables causas: choques inevitables o créditos excedidos.")
        return

    print(f"\n🎯 Top-{len(top)} horarios diversos:")
    for rank, c in enumerate(top, 1):
        _imprimir_horario(rank, c, contexto)

    if len(top) < ga.top_k:
        print(f"\nℹ️  Solo se encontraron {len(top)} horarios suficientemente diversos (pedidos {ga.top_k}).")

    # ── 9. Exportar ────────────────────────────────────────────
    print("\n📤 Exportando horarios...")
    try:
        path_xlsx = exportar_excel(top, contexto, "output/horarios.xlsx", asignaturas_omitidas=omitidas)
        print(f"  ✅ Excel: {path_xlsx}")
    except Exception as e:
        print(f"  ❌ Excel falló: {e}")
    try:
        path_pdf = exportar_pdf(top, contexto, "output/horarios.pdf", asignaturas_omitidas=omitidas)
        print(f"  ✅ PDF:   {path_pdf}")
    except Exception as e:
        print(f"  ❌ PDF falló: {e}")

    # ── 10. Endpoints fallidos ────────────────────────────────
    if datos_raw.get("errores"):
        print(f"\n⚠️  Endpoints fallidos: {datos_raw['errores']}")


if __name__ == "__main__":
    asyncio.run(main())

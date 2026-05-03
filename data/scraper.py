import asyncio
import json
from playwright.async_api import async_playwright

# ──────────────────────────────────────────────
# CONSTANTES
# ──────────────────────────────────────────────
BASE_URL = "https://sum.unmsm.edu.pe/alumnoWebSum"
API_V2   = f"{BASE_URL}/v2"
HDR      = "AlumnoWebSum2026Q1"

ENDPOINTS = {
    "programacion":  f"{API_V2}/matricula/programacion?accion=obtenerProgramacionAsignaturas",
    "prematricula":  f"{API_V2}/reportes/prematricula?accion=obtenerAlumnoPrematricula",
    "alumno":        f"{API_V2}/informacion/perfil?accion=obtenerInformacionAlumno",
    "plan_estudios": f"{API_V2}/planEstudios?accion=obtenerPlanEstudios",
    # prerequisitos vienen dentro de plan_estudios
}


# ──────────────────────────────────────────────
# HELPER: fetch autenticado desde el navegador
# ──────────────────────────────────────────────

async def _fetch(page, url: str, nombre: str) -> dict | None:
    """Ejecuta un fetch desde el contexto autenticado de Playwright.
    Retorna el JSON parseado o None si el endpoint falla."""
    try:
        raw = await page.evaluate(f"""
            async () => {{
                const res = await fetch("{url}", {{
                    method: "GET",
                    headers: {{
                        "X-Requested-With": "{HDR}",
                        "Accept": "application/json"
                    }},
                    credentials: "include"
                }});
                const text = await res.text();
                return {{ status: res.status, body: text }};
            }}
        """)

        print(f"  📡 {nombre}: HTTP {raw['status']}")

        if raw["status"] == 200:
            return json.loads(raw["body"])
        else:
            print(f"  ⚠️  {nombre}: {raw['body'][:150]}")
            return None

    except Exception as e:
        print(f"  ❌ {nombre}: {e}")
        return None


# ──────────────────────────────────────────────
# SCRAPER PRINCIPAL
# ──────────────────────────────────────────────

async def obtener_datos_sum(usuario: str, password: str) -> dict:
    """
    Hace login en el SUM y extrae todos los datos necesarios para el AG:
    - programacion:  secciones y bloques horarios disponibles
    - prematricula:  estado actual de prematrícula del alumno
    - alumno:        perfil, ciclo, promedio ponderado
    - plan_estudios: plan completo con prerequisitos incluidos

    Retorna un dict con todas las respuestas crudas (JSON).
    Los endpoints que fallen quedan como None en el dict.
    """
    resultado = {
        "programacion":  None,
        "prematricula":  None,
        "alumno":        None,
        "plan_estudios": None,
        "errores":       [],
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # ── 1. Login ──────────────────────────────────────────
        print("🌐 Abriendo login...")
        await page.goto(f"{BASE_URL}/login")
        await page.wait_for_load_state("networkidle")

        await page.fill("input[name='login']", usuario)
        await page.fill("input[name='clave']", password)
        await page.click("button.login")
        print("🔑 Credenciales enviadas...")

        # ── 2. Modal "Sí" ─────────────────────────────────────
        try:
            await page.wait_for_selector("button[class='btn green']", timeout=8000)
            await page.click("button[class='btn green']")
            print("✅ Modal cerrado")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
        except:
            print("ℹ️  Sin modal, continuando...")

        # ── 3. Esperar dashboard ───────────────────────────────
        await page.wait_for_url("**/v2/inicio**", timeout=20000)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(4)
        print(f"✅ Dashboard: {page.url}\n")

        # ── 4. Fetch de todos los endpoints ───────────────────
        print("📡 Consultando endpoints...")

        for nombre, url in ENDPOINTS.items():
            data = await _fetch(page, url, nombre)
            if data is not None:
                resultado[nombre] = data
            else:
                resultado["errores"].append(nombre)

        await browser.close()

    # ── 5. Resumen ─────────────────────────────────────────────
    exitosos = [k for k in ENDPOINTS if resultado[k] is not None]
    fallidos  = resultado["errores"]
    print(f"\n✅ Endpoints OK:    {exitosos}")
    if fallidos:
        print(f"⚠️  Endpoints fallidos: {fallidos}")
        print("   Inspecciona con DevTools para confirmar las URLs exactas")

    return resultado
import asyncio
import json
import logging
import os
import sys
import time
from playwright.async_api import TimeoutError as PlaywrightTimeoutError, async_playwright

from .exceptions import (
    SumCredencialesInvalidasError,
    SumDatosIncompletosError,
    SumError,
    SumMantenimientoError,
    SumTimeoutError,
)

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logger = logging.getLogger("sum_scraper")

# ──────────────────────────────────────────────
# CONSTANTES
# ──────────────────────────────────────────────
BASE_URL = "https://sum.unmsm.edu.pe/alumnoWebSum"
API_V2 = f"{BASE_URL}/v2"
HDR = "AlumnoWebSum2026Q1"

ENDPOINTS = {
    "programacion":  f"{API_V2}/matricula/programacion?accion=obtenerProgramacionAsignaturas",
    "prematricula":  f"{API_V2}/reportes/prematricula?accion=obtenerAlumnoPrematricula",
    "alumno":        f"{API_V2}/informacion/perfil?accion=obtenerInformacionAlumno",
    "plan_estudios": f"{API_V2}/planEstudios?accion=obtenerPlanEstudios",
    "historial":     f"{API_V2}/informacion/historial?accion=obtenerHistorialAcademico",
}


# ──────────────────────────────────────────────
# HELPER: Fetch concurrente in-browser
# ──────────────────────────────────────────────

async def _fetch_all_parallel(page, endpoints: dict) -> dict:
    """
    Ejecuta todas las peticiones GET en paralelo dentro del contexto autenticado del navegador
    usando Promise.all nativo en JavaScript.
    Aprovecha la multiplexación HTTP/2 y reduce drásticamente los roundtrips IPC.
    """
    js_code = """
    async ({ endpoints, headerVal }) => {
        const fetchOne = async (key, url) => {
            try {
                const res = await fetch(url, {
                    method: "GET",
                    headers: {
                        "X-Requested-With": headerVal,
                        "Accept": "application/json"
                    },
                    credentials: "include"
                });
                const status = res.status;
                if (status === 200) {
                    const text = await res.text();
                    try {
                        const json = JSON.parse(text);
                        return { key, ok: true, data: json, status };
                    } catch (pe) {
                        return { key, ok: false, status, error: "JSON_PARSE_ERROR" };
                    }
                } else {
                    const errText = await res.text();
                    return { key, ok: false, status, error: errText.slice(0, 200) };
                }
            } catch (e) {
                return { key, ok: false, status: 0, error: e.toString() };
            }
        };

        const entries = Object.entries(endpoints);
        return await Promise.all(entries.map(([k, u]) => fetchOne(k, u)));
    }
    """
    raw_results = await page.evaluate(js_code, {"endpoints": endpoints, "headerVal": HDR})

    resultado = {
        "programacion": None,
        "prematricula": None,
        "alumno": None,
        "plan_estudios": None,
        "historial": None,
        "errores": [],
    }

    statuses = []
    for item in raw_results:
        key = item["key"]
        status = item.get("status", 0)
        statuses.append(status)
        if item.get("ok"):
            resultado[key] = item["data"]
            print(f"  [FETCH-PARALELO] {key}: HTTP 200 OK")
        else:
            resultado["errores"].append(key)
            print(f"  [WARN-PARALELO] {key}: HTTP {status} - {item.get('error')}")

    # Si todos los endpoints respondieron con 5xx, el SUM está en mantenimiento
    if statuses and all(s >= 500 for s in statuses):
        raise SumMantenimientoError("El portal del SUM respondió con errores de servidor (5xx) en todos los endpoints.")

    return resultado


# ──────────────────────────────────────────────
# SCRAPER PRINCIPAL
# ──────────────────────────────────────────────

async def obtener_datos_sum(
    usuario: str,
    password: str,
    headless: bool | None = None,
    timeout_login_ms: int | None = None,
    timeout_fetch_ms: int | None = None,
) -> dict:
    """
    Hace login en el SUM y extrae concurrentemente todos los datos necesarios para el AG:
    - programacion:  secciones y bloques horarios disponibles
    - prematricula:  estado actual de prematrícula del alumno
    - alumno:        perfil, ciclo, promedio ponderado
    - plan_estudios: plan completo con prerequisitos incluidos
    - historial:     asignaturas cursadas y notas aprobadas

    Lanza excepciones de dominio específicas ante fallos (SumCredencialesInvalidasError,
    SumMantenimientoError, SumTimeoutError, SumDatosIncompletosError).
    """
    if not usuario or not password:
        raise SumCredencialesInvalidasError("El usuario y la contraseña no pueden estar vacíos.")

    if headless is None:
        headless = os.getenv("SUM_HEADLESS", "true").lower() in ("true", "1", "yes")

    timeout_login = timeout_login_ms or int(os.getenv("SUM_TIMEOUT_LOGIN", "12000"))
    timeout_fetch = timeout_fetch_ms or int(os.getenv("SUM_TIMEOUT_FETCH", "15000"))

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=headless)
        except Exception as e:
            raise SumError(f"No se pudo inicializar el navegador Playwright: {e}")

        try:
            context = await browser.new_context()
            page = await context.new_page()

            # ── 1. Cargar login ────────────────────────────────────
            print("[SUM] Abriendo portal de login...")
            try:
                resp = await page.goto(f"{BASE_URL}/login", timeout=timeout_login)
                status_code = getattr(resp, "status", None)
                if isinstance(status_code, int) and status_code >= 500:
                    raise SumMantenimientoError(f"El portal del SUM respondió con HTTP {status_code}.")
                await page.wait_for_load_state("networkidle", timeout=timeout_login)
            except PlaywrightTimeoutError:
                raise SumTimeoutError("Tiempo de espera agotado al conectar con la página de inicio del SUM.")
            except Exception as e:
                if isinstance(e, SumError):
                    raise
                raise SumError(f"Error de red al intentar acceder al SUM: {e}")

            # ── 2. Enviar credenciales ─────────────────────────────
            await page.fill("input[name='login']", usuario)
            await page.fill("input[name='clave']", password)
            await page.click("button.login")
            print("[SUM] Credenciales enviadas, validando respuesta...")

            # ── 3. Detección temprana: Éxito vs Error de Login ─────
            async def _check_dashboard():
                try:
                    await page.wait_for_url("**/v2/inicio**", timeout=timeout_login)
                    return ("dashboard", None)
                except Exception:
                    return None

            async def _check_modal():
                try:
                    btn = await page.wait_for_selector("button[class='btn green']", timeout=min(6000, timeout_login))
                    if btn:
                        return ("modal", btn)
                except Exception:
                    pass
                return None

            async def _check_error_alert():
                selectores_error = [
                    ".alert-danger",
                    ".alert.alert-warning",
                    ".swal2-modal",
                    "#divError",
                    ".mensaje-error",
                    "div[class*='alert']",
                ]
                for sel in selectores_error:
                    try:
                        el = await page.wait_for_selector(sel, timeout=timeout_login)
                        if el and await el.is_visible():
                            txt = (await el.inner_text()).strip()
                            if txt:
                                return ("error", txt)
                    except Exception:
                        continue
                return None

            task_dash = asyncio.create_task(_check_dashboard())
            task_modal = asyncio.create_task(_check_modal())
            task_error = asyncio.create_task(_check_error_alert())

            done, pending = await asyncio.wait(
                [task_dash, task_modal, task_error],
                return_when=asyncio.FIRST_COMPLETED,
            )

            for t in pending:
                t.cancel()

            resultado_evento = None
            for t in done:
                res = t.result()
                if res is not None:
                    resultado_evento = res
                    break

            if resultado_evento and resultado_evento[0] == "modal":
                try:
                    await page.click("button[class='btn green']")
                    print("[SUM] Modal cerrado, avanzando al dashboard...")
                    await page.wait_for_url("**/v2/inicio**", timeout=8000)
                except Exception:
                    pass
            elif resultado_evento and resultado_evento[0] == "error":
                mensaje_sum = resultado_evento[1]
                print(f"[SUM] Error de autenticación detectado: {mensaje_sum}")
                raise SumCredencialesInvalidasError(f"Credenciales rechazadas por el SUM: {mensaje_sum}")
            elif not resultado_evento:
                if "login" in page.url:
                    content = await page.content()
                    if any(term in content.lower() for term in ["incorrecta", "incorrecto", "no coincide", "bloqueada"]):
                        raise SumCredencialesInvalidasError("Usuario o contraseña incorrectos en el SUM.")
                    raise SumTimeoutError("Tiempo de espera agotado sin confirmación de inicio de sesión.")

            if "inicio" not in page.url:
                try:
                    await page.wait_for_url("**/v2/inicio**", timeout=5000)
                except PlaywrightTimeoutError:
                    raise SumTimeoutError("No se pudo acceder al dashboard del SUM tras el login.")

            print(f"[SUM] Dashboard activo: {page.url}")

            # ── 4. Fetch paralelo in-browser de todos los endpoints ─
            t_fetch_ini = time.time()
            print("[SUM] Consultando endpoints en paralelo...")
            try:
                resultado = await asyncio.wait_for(
                    _fetch_all_parallel(page, ENDPOINTS),
                    timeout=timeout_fetch / 1000.0,
                )
            except asyncio.TimeoutError:
                raise SumTimeoutError("Tiempo de espera agotado al descargar los datos académicos del SUM.")

            t_duracion_fetch = time.time() - t_fetch_ini
            print(f"[SUM] Consulta paralela completada en {t_duracion_fetch:.2f}s")

            # ── 5. Validación de integridad ─────────────────────────
            if not resultado.get("programacion"):
                raise SumDatosIncompletosError("No se pudo obtener la programación de asignaturas y secciones del SUM.")
            if not resultado.get("prematricula"):
                raise SumDatosIncompletosError("No se pudo obtener la lista de cursos en prematrícula del SUM.")

            return resultado

        finally:
            await browser.close()
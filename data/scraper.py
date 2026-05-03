import asyncio
import json
from playwright.async_api import async_playwright


async def obtener_datos_sum(usuario: str, password: str) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("🌐 Abriendo login...")
        await page.goto("https://sum.unmsm.edu.pe/alumnoWebSum/login")
        await page.wait_for_load_state("networkidle")

        # Credenciales
        await page.fill("input[name='login']", usuario)
        await page.fill("input[name='clave']", password)
        await page.click("button.login")

        print("🔑 Credenciales enviadas...")

        # Cerrar modal con botón verde "Si"
        try:
            await page.click("button[class='btn green']")
            print("✅ Botón 'Si' clickeado")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)
        except:
            print("ℹ️ No apareció modal, continuando...")

        # Esperar dashboard
        await page.wait_for_url("**/v2/inicio**", timeout=20000)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(4)
        print(f"✅ Dashboard cargado: {page.url}")

        # Fetch desde el navegador autenticado
        api_url = "https://sum.unmsm.edu.pe/alumnoWebSum/v2/matricula/programacion?accion=obtenerProgramacionAsignaturas"

        print("📡 Consultando API...")
        raw = await page.evaluate(f"""
            async () => {{
                const res = await fetch("{api_url}", {{
                    method: "GET",
                    headers: {{
                        "X-Requested-With": "AlumnoWebSum2026Q1",
                        "Accept": "application/json"
                    }},
                    credentials: "include"
                }});
                const text = await res.text();
                return {{ status: res.status, body: text }};
            }}
        """)

        await browser.close()

        print(f"📡 Status API: {raw['status']}")

        if raw["status"] == 200:
            return json.loads(raw["body"])
        else:
            raise Exception(f"Error {raw['status']}: {raw['body'][:300]}")
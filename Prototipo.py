import asyncio
import json
import os
from dataclasses import dataclass, field
from typing import List
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()

# --- MODELOS DE DATOS ---

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

def parsear_respuesta(data) -> List[Seccion]:
    secciones_raw = data.get("data", data) if isinstance(data, dict) else data
    if isinstance(secciones_raw, dict):
        for key in secciones_raw:
            if isinstance(secciones_raw[key], list):
                secciones_raw = secciones_raw[key]
                break
    return [parsear_seccion(s) for s in secciones_raw]


# --- LOGIN + FETCH AUTOMÁTICO ---

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


# --- MAIN ---

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

asyncio.run(main())
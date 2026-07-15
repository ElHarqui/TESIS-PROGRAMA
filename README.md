# Optimizador de horarios UNMSM

Sistema que genera automáticamente los mejores horarios de matrícula para un
alumno de la Universidad Nacional Mayor de San Marcos, usando un algoritmo
genético que respeta las restricciones del plan de estudios y las preferencias
del alumno.

Tesis de la Escuela Profesional de Ingeniería de Sistemas, UNMSM.

---

## Cómo funciona

1. Se conecta al Sistema Único de Matrícula (SUM) con las credenciales del
   alumno y descarga la programación del semestre, la prematrícula, el plan de
   estudios, el historial académico y los datos del perfil.
2. Ejecuta un algoritmo genético que evalúa cada horario candidato contra
   restricciones **duras** (choques, prerequisitos, créditos, días
   obligatoriamente libres, rango horario) y **suaves** (turno preferido,
   docentes, disponibilidad de cupos, densidad, días libres deseados).
3. Devuelve los **5 mejores horarios diversos** —no versiones triviales del
   mismo horario— y los muestra en una interfaz web con grilla visual, además
   de permitir descargarlos en Excel y PDF.

---

## Instalación

Requiere **Python 3.10 o superior**.

```bash
# 1. Clonar el repositorio
git clone https://github.com/ElHarqui/TESIS-PROGRAMA.git
cd TESIS-PROGRAMA

# 2. (Opcional pero recomendado) crear un entorno virtual
python -m venv .venv
# En Windows:
.venv\Scripts\activate
# En Linux/macOS:
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Instalar los navegadores de Playwright (necesarios para el scraping del SUM)
playwright install
```

### Configurar credenciales (opcional)

Crear un archivo `.env` en la raíz del proyecto con las credenciales del alumno:

```
LOGIN=tu_codigo_unmsm
PASSWORD=tu_contraseña
```

Estas se usan como **valores por defecto** en el formulario de login de la web.
No son obligatorias en el `.env`: si no están, se ingresan directamente en la
interfaz al abrirla.

---

## Cómo ejecutar el proyecto

**Usá la interfaz web.** Es la manera recomendada, tanto para el alumno final
como para probar el sistema durante la tesis.

```bash
streamlit run app.py
```

La aplicación se abre automáticamente en el navegador en
`http://localhost:8501`. Si no se abre sola, entrar manualmente a esa URL.

### Flujo dentro de la interfaz

1. **Iniciar sesión** desde la barra lateral izquierda: usuario y contraseña
   del SUM (se pre-rellenan con los valores del `.env` si existen). Marcar
   "Forzar re-scraping" solo si los datos en caché están desactualizados.
2. Al conectarse por primera vez, Playwright abre un navegador en segundo
   plano para hacer el scraping del SUM. Tarda unos 30 segundos. Las
   ejecuciones siguientes usan la caché local (válida por 1 hora) y son
   inmediatas.
3. Ir a la pestaña **Preferencias** para configurar los criterios que el
   sistema debe tener en cuenta (ver sección "Preferencias del alumno" abajo).
4. Ir a la pestaña **Mis horarios** y presionar **"Generar 5 horarios"**.
   El algoritmo genético corre en menos de un segundo con los datos ya en
   caché.
5. Revisar los 5 horarios en las sub-pestañas. Cada uno se muestra como
   grilla semanal con métricas de calidad (fitness, ajuste horario, docentes,
   cupos, créditos).
6. Descargar el resultado desde los botones **Descargar Excel** y
   **Descargar PDF** al pie de la pestaña.
7. La pestaña **Datos académicos** muestra el perfil del alumno, la
   prematrícula, el plan de estudios completo y el historial de asignaturas
   cursadas.

### Alternativa: modo consola

Existe una versión de línea de comandos que ejecuta el pipeline completo e
imprime los horarios en la terminal (útil para depuración o scripting):

```bash
python main.py
```

En Windows, si aparecen errores de codificación por los emojis en la salida,
anteponer:

```powershell
$env:PYTHONIOENCODING="utf-8"; python main.py
```

---

## Preferencias del alumno

Se editan desde la sub-pestaña **Preferencias → Horarios** de la interfaz web
y se guardan automáticamente en `data/preferencias_horarios.json`.

### Preferencias SOFT (afectan el puntaje, no descartan horarios)

| Campo | Valores | Efecto |
| ----- | ------- | ------ |
| Turno preferido | `mañana` (7-13), `tarde` (13-18), `noche` (18-22), `indiferente` | Puntúa mejor los horarios cuyos bloques caen en ese rango. |
| Días libres deseados | Lista de días en mayúsculas, ej. `["SABADO"]` | Puntúa mejor los horarios que dejan esos días vacíos, pero puede asignarlos si el balance mejora. |
| Densidad | `compacto`, `distribuido`, `indiferente` | `compacto` premia menos días con clase; `distribuido` premia más días. |

### Restricciones estrictas HARD (descartan horarios que las violen)

Configurables por el alumno desde el bloque "Restricciones estrictas" de la
misma pestaña. Se aplican como reglas duras: cualquier horario que las viole
se descarta.

| Campo | Efecto |
| ----- | ------ |
| Días obligatoriamente libres | Ningún horario tendrá clase en los días marcados. Ej: si el alumno trabaja los domingos, marca `DOMINGO`. |
| Hora mínima obligatoria | Ningún bloque puede empezar antes de esa hora. Ej: `08:00` descarta clases que empiecen 07:00. |
| Hora máxima obligatoria | Ningún bloque puede terminar después de esa hora. Ej: `20:00` descarta clases que terminen 22:00. |

Ambas horas se activan con un checkbox y se dejan en blanco si no se quiere
usar esa restricción. **Cuidado**: si se marcan demasiadas restricciones
estrictas, puede no existir ningún horario válido. El sistema avisa cuando
eso ocurre.

### Preferencias de docentes

Se editan desde la sub-pestaña **Preferencias → Docentes** y se guardan en
`data/preferencias_docentes.json`. Un slider de 0 a 1 por cada docente único
de la prematrícula:

- `0.0` = evitar a toda costa (penaliza fuerte)
- `0.5` = neutral (valor por defecto)
- `1.0` = preferido

---

## Configuración del algoritmo genético

Los pesos del fitness y los parámetros del GA viven en `config_ga.json` en la
raíz del proyecto. Se pueden ajustar sin tocar código:

```json
{
  "fitness": {
    "peso_horarios": 0.4, "peso_docentes": 0.3, "peso_cupos": 0.3,
    "sub_peso_turno": 0.34, "sub_peso_dias_libres": 0.33, "sub_peso_densidad": 0.33
  },
  "ga": {
    "tamano_poblacion": 100, "generaciones": 50, "tasa_mutacion": 0.15,
    "tamano_torneo": 3, "elitismo": 5, "top_k": 5, "distancia_minima": 1,
    "seed": 42
  },
  "alumno": { "max_creditos": 24 }
}
```

Los defaults están bien para un uso típico. Los pesos del fitness suman 1.0
para que el puntaje final quede en el rango [0, 1].

---

## Estructura del proyecto

```
TESIS-PROGRAMA/
├── app.py                  # Interfaz web (Streamlit) — RECOMENDADO
├── main.py                 # CLI equivalente
├── config.py               # Loader de config_ga.json
├── config_ga.json          # Pesos del fitness y parámetros del GA
├── requirements.txt
│
├── data/                   # Adquisición y procesamiento de datos del SUM
│   ├── scraper.py            # Login y consulta de endpoints (Playwright)
│   ├── parser.py             # Conversión de JSON crudo a dataclasses
│   └── cache.py              # Caché local con TTL
│
├── models/                 # Entidades de dominio
│   ├── bloque.py             # BloqueHorario
│   ├── seccion.py            # Sección
│   └── cromosoma.py          # Solución candidata del GA
│
├── fitness/                # Evaluación de horarios
│   ├── contexto.py           # ContextoAlumno + PreferenciasHorario
│   ├── preferencias.py       # Loaders de los JSON de preferencias
│   ├── hard_constraints.py   # 6 restricciones duras
│   ├── soft_constraints.py   # 3 preferencias suaves
│   └── evaluator.py          # Fórmula del fitness
│
├── genetic/                # Motor evolutivo
│   ├── population.py         # Población inicial
│   ├── selection.py          # Selección por torneo y ruleta
│   ├── operators.py          # Cruce y mutación
│   └── ga_engine.py          # Bucle generacional + top-K diverso
│
├── output/                 # Presentación y exportación
│   ├── visualizer.py         # Grilla semanal
│   └── exporter.py           # Excel y PDF
│
├── prediccion/             # Módulo predictivo de vacantes (STANDBY)
│   ├── ranking.py            # Loader del ranking ponderado
│   ├── demanda.py            # Estimador de demanda por sección
│   └── README.md             # Estado y plan de activación
│
├── .streamlit/config.toml  # Tema y configuración de Streamlit
├── .env                    # Credenciales del SUM (no versionado)
│
└── data/
    ├── preferencias_horarios.json   # Preferencias del alumno (no versionado)
    └── preferencias_docentes.json   # Scores manuales de docentes (no versionado)
```

Para más detalle sobre la arquitectura y decisiones de diseño, ver
`CONTEXTO_AVANCE.md`.

---

## Dependencias

- `streamlit` — interfaz web
- `playwright` — automatización del navegador para el scraping
- `python-dotenv` — carga de variables desde `.env`
- `openpyxl` — export a Excel
- `reportlab` — export a PDF
- `pdfplumber` — lectura del ranking ponderado (módulo predictivo)
- `nest-asyncio` — permitir loops asíncronos anidados (Playwright dentro de Streamlit)

Todas se instalan con `pip install -r requirements.txt`.

---

## Notas de seguridad

- El archivo `.env`, la caché del scraping (`data/cache.json`) y las
  preferencias personales (`data/preferencias_*.json`) contienen datos
  sensibles del alumno y están en `.gitignore`. No subir a repositorios
  públicos.
- Los archivos exportados en `output/horarios.xlsx` y `output/horarios.pdf`
  también contienen datos personales y están en `.gitignore`.

---

## Autor

Sebastian Leonardo Peralta Silvano — Código 22200033
Escuela Profesional de Ingeniería de Sistemas, UNMSM.

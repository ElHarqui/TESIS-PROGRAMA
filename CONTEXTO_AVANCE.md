# Contexto de Avance — Tesis: Optimizador de Matrícula UNMSM con Algoritmo Genético

> Documento de contexto para asistentes LLM. Refleja el estado REAL del proyecto.
> Última actualización: mayo 2026.

---

## 1. Resumen ejecutivo

Sistema que genera **horarios de matrícula óptimos** para alumnos de la Universidad Nacional
Mayor de San Marcos (UNMSM). Extrae datos del Sistema Único de Matrícula (SUM) mediante web
scraping y usa un **algoritmo genético (GA)** para producir **~5 horarios diversos** que se
ajustan a las preferencias del alumno y a las condiciones reales (cupos, prerequisitos,
choques horarios).

**Objetivo de la tesis**: crear una herramienta que, según el alumno, le genere varios
horarios (aproximadamente 5) ajustados a sus gustos y a las distintas condiciones que
se le presentan — en particular el promedio ponderado, que en UNMSM determina el turno
de matrícula.

**Estado global**: el sistema completo (scraping → parsing → GA → 5 horarios → visualización
y export a Excel/PDF) está **operativo y probado end-to-end**. Se entrega como CLI
(`python main.py`) y como **interfaz web Streamlit** (`streamlit run app.py`). Falta:
módulo predictivo de vacantes (en STANDBY por falta de datos, ver §17).

---

## 2. El problema de dominio

### 2.1 Matrícula en UNMSM

El alumno se matricula eligiendo **secciones** de las **asignaturas** de su plan de estudios.
Cada sección tiene uno o varios **bloques horarios** (teoría, práctica, laboratorio), un
**docente**, un **cupo máximo** (`topeAlumnos`) y una cantidad de **matriculados** actuales.

### 2.2 Sistema de turnos por ponderado (clave para la tesis)

La matrícula NO es por orden de llegada. La UNMSM separa a los alumnos en **turnos según su
promedio ponderado**, en **rangos de 2 puntos**:

- Ponderado 18–20 → se matriculan **primero**
- Ponderado 16–18 → segundo turno
- Ponderado 14–16 → tercer turno
- ... y así sucesivamente

**Consecuencia**: cuando a un alumno le toca su turno, las secciones ya tienen cierta
ocupación por los alumnos de turnos anteriores. Predecir cuántos cupos quedarán disponibles
al momento del turno del alumno es el **módulo predictivo de demanda** (planeado, ver §9).

### 2.3 Restricciones del problema

- **Choques horarios**: dos bloques no pueden solaparse en día + hora.
- **Prerequisitos**: una asignatura solo se puede tomar si su prerequisito está aprobado.
- **Cupos**: las secciones tienen capacidad limitada.
- **Límite de créditos**: máximo 24 créditos por ciclo (configurable).
- **Preferencias del alumno**: turnos horarios, docentes, días libres.

---

## 3. Arquitectura del sistema

Aplicación en capas, escrita en **Python 3.13**. Cada capa es un paquete:

```
TESIS PROGRAMA/
├── main.py              # CLI: scraping → parsing → GA → muestra 5 horarios
├── app.py               # UI Streamlit: login + horarios + preferencias + descargas
├── config.py            # Loader de config_ga.json
├── data/                # Capa de datos: adquisición y transformación
├── models/              # Capa de dominio: entidades centrales
├── fitness/             # Capa de evaluación: restricciones y scoring
├── genetic/             # Capa de algoritmo genético
├── prediccion/          # Módulo predictivo de vacantes (⏸️ STANDBY — no integrado)
└── output/              # Capa de salida: grilla CLI + Excel + PDF
```

**Dependencias actuales**: `playwright` (scraping), `python-dotenv` (variables de entorno),
`openpyxl` (export Excel), `reportlab` (export PDF), `pdfplumber` (lectura del ranking),
`streamlit` (UI web), `nest-asyncio` (loops anidados para Playwright dentro de Streamlit).

---

## 4. Estado de implementación por capa

| Capa | Estado | Detalle |
|------|--------|---------|
| `data/` | ✅ 100% | Scraper Playwright + parsers de 5 endpoints + cache JSON con TTL |
| `models/` | ✅ 100% | `BloqueHorario`, `Seccion`, `Cromosoma` con sus métodos y propiedades |
| `fitness/` | ✅ ~95% | 4 hard constraints + 3 soft constraints + contexto + evaluador |
| `genetic/` | ✅ 100% | Población inicial + selección + operadores + motor + top-K diverso |
| `prediccion/` | ⏸️ STANDBY | Implementado pero **NO integrado**: faltan datos reales (ver §17) |
| `output/` | ✅ 100% | Grilla CLI + Excel (5 hojas) + PDF (5 páginas, A4 landscape) |
| `app.py` (UI) | ✅ 100% | Streamlit: login, dashboard de horarios, edición de preferencias, descargas |

---

## 5. Flujo de ejecución end-to-end

Al correr `python main.py`:

1. **Carga de credenciales**: lee `LOGIN` y `PASSWORD` desde `.env`.
2. **Caché**: si `data/cache.json` existe y tiene < 1 hora, usa los datos cacheados.
   Si no, hace scraping.
3. **Scraping** (`data/scraper.py`): login con Playwright en el SUM y consulta de 5 endpoints
   de la API interna (`programacion`, `prematricula`, `alumno`, `plan_estudios`, `historial`).
4. **Parsing** (`data/parser.py`): convierte el JSON crudo en objetos de dominio.
5. **Construcción de contexto**: arma un `ContextoAlumno` con prerequisitos, asignaturas
   aprobadas, límite de créditos y preferencias (docentes y horarios).
6. **Generación de población inicial** (`genetic/population.py`): 100 cromosomas aleatorios.
7. **Ejecución del GA** (`genetic/ga_engine.py`): 50 generaciones de evolución.
8. **Extracción del top-5 diverso**: selecciona 5 horarios buenos y distintos entre sí.
9. **Presentación CLI** (`output/visualizer.py`): imprime cada horario como grilla semanal
   LUN-SAB × horas + leyenda con asignaturas y docentes.
10. **Exportación** (`output/exporter.py`): genera `output/horarios.xlsx` (5 hojas, una por
    horario, con celdas coloreadas por asignatura) y `output/horarios.pdf` (5 páginas A4
    landscape, una por horario).

Tiempo: ~0.5 s con caché; ~30 s si scrapea (abre navegador).

---

## 6. Modelos de dominio (`models/`)

### `BloqueHorario` (`models/bloque.py`)
Un bloque de clase. Campos: `codAsignatura`, `codSeccion`, `codDocente`, `horario`, `dia`,
`horaInicio`, `horaFin`, `codAula`, `tipo`, `desTipo`.
- `hora_inicio_int` / `hora_fin_int`: convierten "HH:MM" a minutos.
- `choca_con(otro)`: detecta solapamiento horario con otro bloque.

### `Seccion` (`models/seccion.py`)
Una sección de asignatura. Campos: `ciclo`, `codAsignatura`, `desAsignatura`, `creditos`,
`codSeccion`, `codDocente`, `nomDocente`, `apePatDocente`, `apeMatDocente`, `topeAlumnos`,
`matriculados`, `bloques` (lista de `BloqueHorario`).
- `docente_completo`: nombre completo del docente.
- `disponibilidad`: porcentaje de cupos libres `(tope - matriculados) / tope * 100`.

### `Cromosoma` (`models/cromosoma.py`)
**Una solución candidata = un horario completo.** Es una lista de `Seccion`, una por cada
asignatura que el alumno quiere matricular.

### Modelos de datos auxiliares (`data/parser.py`)
- `DatosAlumno`: perfil del alumno (ciclo, ponderado, plan, etc.).
- `AsignaturaPlan`: una asignatura del plan de estudios con su prerequisito.
- `RegistroHistorial`: una asignatura cursada con su calificación.

---

## 7. Sistema de fitness (`fitness/`)

El **fitness** es un número entre 0 y 1 que mide qué tan bueno es un horario (cromosoma).

### 7.1 Hard constraints (`fitness/hard_constraints.py`)

Si un cromosoma viola CUALQUIER hard constraint, su fitness es **0.0** (descalificado).
Son violaciones físicamente imposibles, no negociables:

| Constraint | Falla cuando |
|------------|--------------|
| `verificar_choques` | Dos bloques se solapan en día + hora |
| `verificar_asignaturas_unicas` | Hay dos secciones de la misma asignatura |
| `verificar_limite_creditos` | La suma de créditos supera el máximo (24) |
| `verificar_prerequisitos` | Una asignatura tiene prerequisito no aprobado |
| `verificar_dias_libres_obligatorios` | Un bloque cae en un día marcado como obligatoriamente libre por el alumno |
| `verificar_rango_horario` | Un bloque inicia antes de `hora_min` o termina después de `hora_max` |

Los dos últimos son **restricciones estrictas configurables por el alumno**
(distintas de las cuatro primeras, que son intrínsecas al problema). Se activan
cuando el alumno completa los campos correspondientes en
`preferencias_horarios.json` (o en la sub-pestaña "Preferencias" de la UI).
Si no se configuran (defaults: lista vacía y `None`), no aplican y no descalifican.

### 7.2 Soft constraints (`fitness/soft_constraints.py`)

Si el cromosoma pasa todos los hard, se calculan 3 scores suaves (0-1 cada uno):

| Soft constraint | Qué mide |
|-----------------|----------|
| `preferencia_horarios` | Ajuste a turno preferido + días libres + densidad de clases |
| `preferencia_docentes` | Promedio de scores de los docentes del cromosoma |
| `preferencia_cupos` | Disponibilidad de cupos (promedio de `disponibilidad`) |

`preferencia_horarios` es a su vez el promedio de 3 sub-scores:
- **turno**: % de bloques cuyo inicio cae en el rango horario preferido
  (mañana 7-13, tarde 13-18, noche 18-22).
- **días libres**: fracción de días deseados que efectivamente quedan sin clase.
- **densidad**: `compacto` premia menos días con clase; `distribuido` premia más.

### 7.3 Fórmula del fitness (`fitness/evaluator.py`)

```
Si falla algún hard constraint → fitness = 0.0
Si no:
    fitness = 0.4 × preferencia_horarios
            + 0.3 × preferencia_docentes
            + 0.3 × preferencia_cupos
```

Los pesos (0.4 / 0.3 / 0.3) suman 1.0, así que el fitness siempre cae en [0, 1].
**Estos pesos viven en `config_ga.json`** (ver §16), no están hardcodeados.

**Razón de los pesos**: el horario afecta la vida diaria del alumno durante todo el ciclo
(por eso pesa más); docentes y cupos son importantes pero secundarios. El peso de cupos
es alto porque correlaciona con la probabilidad real de conseguir la sección bajo el
sistema de turnos.

### 7.4 `ContextoAlumno` (`fitness/contexto.py`)

Objeto que encapsula TODO lo que las constraints necesitan saber del alumno:
`prerequisitos`, `aprobados`, `max_creditos`, `scores_docentes`, `prefs_horario`.
Se construye una vez y se reutiliza durante toda la evolución (inmutable).

---

## 8. El algoritmo genético (`genetic/`)

### 8.1 Representación

- **Gen** = una sección elegida para una asignatura.
- **Cromosoma** = un horario completo (lista de secciones).
- **Población** = 100 cromosomas.

### 8.2 Población inicial (`genetic/population.py`)

`generar_poblacion_inicial`: crea 100 cromosomas; cada uno elige una sección aleatoria por
cada asignatura de la prematrícula. Filtra "secciones fantasma" (sin horario válido). Si una
asignatura no tiene ninguna sección disponible, la **omite** (no es obligatorio matricularse
en todas si no hay cursos). Devuelve `(poblacion, asignaturas_omitidas)`.

### 8.3 Loop generacional (`genetic/ga_engine.py` — `ejecutar_ga`)

Por cada una de las 50 generaciones:

1. **Evaluar** el fitness de cada cromosoma.
2. **Elitismo**: los 5 mejores pasan intactos a la siguiente generación (garantiza no
   retroceder).
3. **Reproducción**: se llena el resto (95 individuos) con:
   - **Selección por torneo**: se eligen 3 cromosomas al azar, gana el de mayor fitness.
   - **Cruce uniforme**: para cada asignatura, el hijo hereda la sección del padre 1 o
     del padre 2 al azar.
   - **Mutación**: con probabilidad 15% por gen, una sección se reemplaza por otra
     aleatoria de la misma asignatura.

### 8.4 Operadores (`genetic/operators.py`, `genetic/selection.py`)

- `seleccion_torneo` (tamaño 3) — robusta ante muchos cromosomas con fitness 0.
- `seleccion_ruleta` — alternativa, probabilidad proporcional al fitness.
- `cruce` — cruce uniforme por asignatura.
- `mutacion` — reemplazo de sección con tasa configurable.

### 8.5 Extracción del top-5 diverso (`genetic/ga_engine.py` — `top_k_diversos`)

Al terminar la evolución no se devuelven los 5 de mayor fitness (podrían ser casi idénticos),
sino 5 cromosomas **buenos Y distintos**. Algoritmo greedy: toma el mejor, y luego cada
siguiente solo si difiere en al menos 1 sección de todos los ya elegidos. La distancia entre
cromosomas se mide como número de secciones diferentes.

### 8.6 Parámetros del GA (definidos en `config_ga.json`)

| Parámetro | Valor actual |
|-----------|--------------|
| Tamaño de población | 100 |
| Generaciones | 50 |
| Tasa de mutación | 0.15 |
| Tamaño de torneo | 3 |
| Elitismo | 5 |
| Top-K (horarios devueltos) | 5 |
| Distancia mínima de diversidad | 1 sección |
| Seed | 42 (`null` para no determinista) |

Estos parámetros se cargan desde `config_ga.json` (ver §16); no están hardcodeados.

---

## 9. Preferencias del alumno

Se capturan en dos archivos JSON editables (ignorados por git, son personales):

### `data/preferencias_docentes.json`
```json
{
  "scores": { "codDocente": 0.9, "otroCod": 0.1 }
}
```
Score 0.0 = evitar, 0.5 = neutral (default si no está mapeado), 1.0 = preferido.

### `data/preferencias_horarios.json`
```json
{
  "turno_preferido": "noche",
  "dias_libres_deseados": ["SABADO"],
  "densidad": "compacto",

  "dias_libres_obligatorios": ["DOMINGO"],
  "hora_min": "08:00",
  "hora_max": "22:00"
}
```

**Campos SOFT** (penalizan el fitness, no descalifican):
- `turno_preferido`: `manana` | `tarde` | `noche` | `indiferente`.
- `dias_libres_deseados`: lista de días en mayúsculas.
- `densidad`: `compacto` | `distribuido` | `indiferente`.

Cualquier valor `indiferente` neutraliza ese sub-score (cuenta como 0.5).

**Campos HARD** (descalifican al cromosoma que las viole):

- `dias_libres_obligatorios`: lista de días donde NO se acepta ningún bloque.
  Vacío = sin restricción.
- `hora_min`: hora mínima `"HH:MM"` antes de la cual no se acepta ningún bloque.
  `null` o ausente = sin restricción.
- `hora_max`: hora máxima `"HH:MM"` después de la cual no se acepta ningún bloque.
  `null` o ausente = sin restricción.

Los campos HARD son opcionales: JSONs viejos sin ellos siguen funcionando sin cambios
(defaults: lista vacía y `None`).

---

## 10. Datos del SUM: estructura y hallazgos

### Endpoints consultados
| Endpoint | Contenido |
|----------|-----------|
| `programacion` | Secciones disponibles este semestre con sus bloques horarios |
| `prematricula` | Asignaturas que el alumno pre-cargó (define qué horarios armar) |
| `alumno` | Perfil: ciclo, promedio ponderado, plan, situación académica |
| `plan_estudios` | Plan completo con prerequisitos de cada asignatura |
| `historial` | Asignaturas cursadas con calificaciones |

### Hallazgos importantes (descubiertos analizando datos reales)

1. **El historial NO incluye `codDocente`**. Solo el número de sección. Por eso no se puede
   construir automáticamente un score de docentes desde las notas pasadas — las preferencias
   de docentes deben cargarse manualmente.
2. **Existen "secciones fantasma"**: secciones que el SUM devuelve con `dia = "NR"`,
   `horaInicio = None` y `topeAlumnos = 1`. Son placeholders sin horario real. Se filtran
   antes de generar la población.
3. **Prerequisitos siempre 1-a-1**: en el plan analizado, cada asignatura tiene como máximo
   un prerequisito (una asignatura específica), nunca prerequisitos por créditos ni por
   grupos. Esto simplifica el modelo.
4. **Cupos saturados**: en ciclos avanzados (8-10), muchas secciones ya están al 100% de
   ocupación en el snapshot del scraping. Por eso `verificar_cupos` NO es hard constraint —
   se convirtió en soft (`preferencia_cupos`): un cupo lleno hoy puede liberarse en otro
   turno de matrícula.

---

## 11. Decisiones de diseño relevantes

- **`ContextoAlumno` como objeto de contexto**: encapsula todo lo que las constraints
  necesitan; evita pasar muchos parámetros sueltos y es inmutable durante la evolución.
- **Cupos como soft, no hard**: clave para que la herramienta funcione. Con cupos como hard,
  el 100% de los cromosomas resultaban inválidos en ciclos avanzados.
- **Cruce uniforme por asignatura**: no hay correlación posicional entre asignaturas, así
  que el cruce uniforme mezcla mejor el espacio que un cruce de un punto.
- **Top-K diverso en vez de top-K por fitness**: garantiza que los 5 horarios entregados
  sean genuinamente distintos, no variantes triviales del mismo.
- **Matrícula no obligatoria completa**: si una asignatura no tiene secciones disponibles,
  se omite del horario; el sistema sigue funcionando con las demás.

---

## 12. Lo que falta (roadmap)

| Pendiente | Descripción | Estado |
|-----------|-------------|--------|
| **Módulo predictivo de vacantes** | Estimar cuántos cupos quedarán libres al turno del alumno (refinaría `preferencia_cupos`). Hay código listo en `prediccion/` y feature flag en `config_ga.json`, pero NO está integrado al pipeline hasta tener datos reales (ver §17). | ⏸️ STANDBY |

✅ **Login dinámico** — implementado en `app.py`: form de credenciales que reemplaza el
`.env` (que ahora actúa solo como fallback).

✅ **Interfaz de usuario** — implementada en `app.py` con Streamlit. Ver §18.

✅ **Configuración externa** — ya implementada: pesos del fitness y parámetros del GA
viven en `config_ga.json` (ver §16).

✅ **Capa `output/`** — ya implementada: grilla CLI visual + export a Excel (5 hojas) +
export a PDF (5 páginas A4 landscape, coloreado por asignatura).

---

## 13. Cómo ejecutar

```bash
pip install -r requirements.txt
playwright install
# Crear .env con LOGIN y PASSWORD del SUM
python main.py
```

En Windows, anteponer `PYTHONIOENCODING=utf-8` para la salida con emojis.

---

## 14. Glosario

| Término | Significado |
|---------|-------------|
| SUM | Sistema Único de Matrícula de la UNMSM |
| Sección | Una "instancia" de una asignatura con docente, horario y cupo propios |
| Bloque horario | Una franja de clase concreta (día + hora inicio + hora fin) |
| Cromosoma | Un horario completo candidato (solución del GA) |
| Fitness | Puntaje 0-1 de calidad de un horario |
| Hard constraint | Restricción inviolable; su incumplimiento descalifica el horario |
| Soft constraint | Preferencia; su incumplimiento solo baja el puntaje |
| Ponderado | Promedio ponderado del alumno; determina su turno de matrícula |
| Turno de matrícula | Franja en que un grupo de alumnos puede matricularse, según ponderado |
| Elitismo | Preservar los mejores cromosomas intactos entre generaciones |
| Sección fantasma | Sección del SUM sin horario real (placeholder) |

---

## 15. Contexto académico

Tesis de la Escuela de Ingeniería de Sistemas, UNMSM (plan 2018). El caso de prueba es un
alumno de ciclo 9 con promedio ponderado 14.4 (tercer turno de matrícula). El aporte
central de la tesis es modelar la generación de horarios como un problema de optimización
multi-objetivo resuelto con algoritmo genético, considerando las condiciones reales del
proceso de matrícula UNMSM — en especial el sistema de turnos por ponderado.

---

## 16. Configuración del sistema (`config_ga.json`)

Los pesos del fitness y los parámetros del GA están externalizados en `config_ga.json`
(raíz del proyecto), para tunearlos sin tocar código. `config.py` lo carga; si el archivo
falta o le faltan campos, se completan con defaults.

```json
{
  "fitness": {
    "peso_horarios": 0.4,
    "peso_docentes": 0.3,
    "peso_cupos": 0.3,
    "sub_peso_turno": 0.34,
    "sub_peso_dias_libres": 0.33,
    "sub_peso_densidad": 0.33
  },
  "ga": {
    "tamano_poblacion": 100,
    "generaciones": 50,
    "tasa_mutacion": 0.15,
    "tamano_torneo": 3,
    "elitismo": 5,
    "top_k": 5,
    "distancia_minima": 1,
    "seed": 42
  },
  "alumno": { "max_creditos": 24 }
}
```

- `fitness.peso_*`: ponderan los 3 soft constraints (idealmente suman 1.0).
- `fitness.sub_peso_*`: ponderan los 3 sub-criterios de `preferencia_horarios`.
- `ga.*`: parámetros del algoritmo genético. `seed: null` → corridas no deterministas.
- `alumno.max_creditos`: tope de créditos por ciclo (hard constraint).

`config_ga.json` SÍ se versiona en git (es config compartida, no datos personales —
a diferencia de `data/preferencias_*.json` que son personales y están en `.gitignore`).

---

## Archivos de configuración — resumen

| Archivo | Versionado en git | Contenido |
|---------|-------------------|-----------|
| `.env` | ❌ No | Credenciales del SUM (LOGIN, PASSWORD) |
| `config_ga.json` | ✅ Sí | Pesos del fitness y parámetros del GA |
| `data/preferencias_docentes.json` | ❌ No | Scores de docentes (personal) |
| `data/preferencias_horarios.json` | ❌ No | Preferencias de horario (personal) |
| `data/cache.json` | ❌ No | Caché del scraping (datos personales del alumno) |
| `data/ranking_ponderado_*.csv` | ❌ No | Ranking de la facultad (datos de muchos alumnos) |
| `pdf/` | ❌ No | PDFs fuente del ranking, historial, etc. |

---

## 17. Módulo predictivo de vacantes (`prediccion/`) — ⏸️ STANDBY (feature flag)

### Estado

Implementado y probado AISLADAMENTE, pero **NO está integrado al pipeline principal**.
Se controla por la flag `prediccion.activada` en `config_ga.json` (default: `false`).
Mientras esté en `false`, el sistema funciona sin predictivo y `preferencia_cupos`
usa el cálculo crudo de disponibilidad.

### Datos disponibles HOY

- ✅ Ranking ponderado **2025-0** (1541 alumnos, 3 escuelas mezcladas).
- ✅ **875 matriculados en E.P. Ingeniería de Sistemas** para el semestre actual.
- ❌ Ranking 2026-I filtrado por Ing. Sistemas.
- ❌ Matrícula real por ciclo.
- ❌ Encuesta de docentes.

### Por qué no está integrado

El modelo predictivo produciría resultados engañosos sin tres piezas de información
que aún no tenemos:

1. **Ranking del semestre objetivo (2026-I)** filtrado por Ing. Sistemas. El ranking
   actual disponible es de 2025-0 y mezcla las 3 escuelas de la facultad (los códigos
   de alumno no permiten distinguirlas — todos comparten el prefijo `XX200YYY`).

2. **Matrícula real por ciclo en el semestre actual**. La inferencia de ciclo desde el
   código de alumno asume avance regular (2 ciclos por año), lo cual no refleja
   atrasados ni adelantados.

3. **Comportamiento multi-ciclo de los alumnos**. En UNMSM un alumno cursa asignaturas
   de varios ciclos a la vez (ej. el alumno objetivo está en ciclo 9 pero su
   prematrícula tiene materias de ciclos 8, 9 y 10). El modelo V1 asume que cada
   alumno cursa solo su ciclo nominal — falso en la realidad.

### Qué está implementado en `prediccion/`

- **`ranking.py`**:
  - `cargar_ranking(path) → List[AlumnoRanking]` — lee el CSV.
  - `inferir_anio_ingreso(codigo) → int | None` — extrae año del prefijo del código.
  - `inferir_ciclo_estimado(codigo, año_referencia) → int | None` — fórmula:
    `ciclos_completos = (año_ref - año_ingreso) × 2`, ciclo actual = `ciclos_completos + 1`.

- **`demanda.py`** — `EstimadorDemanda` con Enfoque 1+3 (V1 determinista):
  - **Enfoque 1 (quién compite)**: para una asignatura de ciclo C, los competidores son
    los alumnos del ranking en ciclo C (ajustado por `delta_ciclos`) con ponderado mayor
    al del alumno objetivo.
  - **Enfoque 3 (cómo se reparten)**: la demanda se distribuye entre las secciones de la
    asignatura proporcionalmente a su `topeAlumnos`.
  - `score_cupo(seccion) → float 0-1` (probabilidad estimada de conseguir cupo).
  - `reporte_asignatura(cod)` — diagnóstico con competidores, capacidad, ratio.

### Hallazgo del test E2E con el caso real

Con el ranking 2025-0 disponible, proyectando a 2026-I (`delta_ciclos=2`):

- Las 5 asignaturas de ciclo 9 de la prematrícula muestran **179 competidores** con
  ponderado mayor al objetivo (14.402) y capacidades totales 136-159 → ratio
  demanda/capacidad de 1.13 a 1.32. **Score 0.0 (sobre-demanda).** Refleja una
  realidad esperable: el alumno tendrá problemas para tomar esas asignaturas.

- Las 3 asignaturas de ciclos 8 y 10 dan **0 competidores** porque la inferencia
  determinista solo produce ciclos impares para 2025-I. Score 1.0 (cupo garantizado),
  **lo cual es incorrecto**. Esto es la manifestación del problema multi-ciclo
  descrito arriba.

### Modelo de referencia acordado (V1.5, NO implementado en código todavía)

Cuando se decida activar (cambiar la flag), el modelo discutido fue:

1. **Escalar la distribución de ciclos** del ranking 2025-0 (1541 alumnos) al
   tamaño real de Ing. Sistemas (875). Factor: `875 / 1541 ≈ 0.568`.
2. **Banda de ciclo con pesos**: para una asignatura de ciclo C, los alumnos en
   ciclo nominal (C-delta) compiten con peso `1.0`; los de ciclos vecinos
   (C-delta ± 1) compiten con peso `0.5`. Refleja que en UNMSM los alumnos cursan
   asignaturas fuera de su ciclo nominal.
3. **Proyección de semestre**: ranking 2025-I → 2026-I = `delta_ciclos=2`.
4. **Reparto entre secciones** proporcional al `topeAlumnos`.
5. **Disclaimer obligatorio** en el output del top-5 marcando la imprecisión de
   los datos.

Todos los parámetros del modelo viven en `config_ga.json` → sección `prediccion`:

```json
"prediccion": {
  "activada": false,
  "ranking_path": "data/ranking_ponderado_2025_0.csv",
  "ranking_anio_referencia": 2025,
  "semestre_target_delta_ciclos": 2,
  "total_alumnos_escuela": 875,
  "total_alumnos_ranking_origen": 1541,
  "peso_ciclo_nominal": 1.0,
  "peso_ciclo_vecino": 0.5
}
```

### Plan de activación (cuando estén los datos)

1. Cambiar `prediccion.activada` a `true` en `config_ga.json`.
2. Extender `EstimadorDemanda` para usar la banda con pesos y el factor de escala
   (hoy usa ciclo exacto sin escala — implementación V1, no V1.5).
3. Agregar `estimador_demanda: Optional[EstimadorDemanda]` al `ContextoAlumno`.
4. Modificar `preferencia_cupos` para usar el estimador si la flag está activa
   (fallback al cálculo crudo si no).
5. Construir el estimador en `main.py` y pasarlo al contexto.
6. Mostrar el disclaimer en el output cuando la flag esté activa.

Ver `prediccion/README.md` para más detalle sobre limitaciones y plan de V2.

---

## 18. Interfaz web (`app.py`) — Streamlit

### Cómo ejecutar
```bash
pip install -r requirements.txt
playwright install
streamlit run app.py
```

Abre el navegador en `http://localhost:8501`.

### Layout

- **Sidebar**:
  - Si no hay sesión activa: formulario de login (usuario + contraseña). Pre-rellena
    con `LOGIN` y `PASSWORD` del `.env` si existen (fallback).
  - Si hay sesión: muestra nombre/código del alumno + botón "Re-scrapear (forzar)" +
    "Cerrar sesión".
  - Checkbox **"Forzar re-scraping"** antes de conectar para ignorar caché.

- **Pestañas principales** (después del login):

  1. **📅 Mis horarios**:
     - Botón "🧬 Generar 5 horarios" → ejecuta el GA (~0.3s con caché).
     - Muestra status: válidos al inicio → válidos al final, duración.
     - Asignaturas omitidas en un expander (si las hay).
     - **Pestaña por horario** con: 5 métricas (fitness, horarios, docentes, cupos,
       créditos), **grilla HTML coloreada** y tabla-leyenda.
     - **Descargas**: botones `⬇️ Excel` y `⬇️ PDF` con los binarios reales.

  2. **⚙️ Preferencias**:
     - **Sub-pestaña Docentes**: un slider 0-1 por cada docente único en la
       prematrícula (lista construida desde el SUM). Guarda a
       `data/preferencias_docentes.json`.
     - **Sub-pestaña Horarios**: selectbox turno preferido, multiselect días libres,
       selectbox densidad. Guarda a `data/preferencias_horarios.json`.

  3. **🎓 Datos académicos**:
     - Métricas (ciclo, ponderado, plan) + escuela/facultad/situación.
     - Tabla de prematrícula.
     - Expander: tabla del plan completo (con prerequisitos).
     - Expander: tabla del historial completo (con notas).

### Decisiones técnicas

- **`nest-asyncio`**: Playwright es async; Streamlit corre en su propio loop.
  `nest_asyncio.apply()` permite anidar loops para que `asyncio.run(...)` funcione
  desde callbacks de Streamlit.
- **`session_state`** persiste durante la sesión del usuario: `datos_raw`, `alumno`,
  `plan`, `secciones`, `prematricula`, `historial`, `horarios` (cromosomas del top-K),
  `fitness_fin`, `omitidas`, etc.
- **Grilla HTML inline**: la grilla del horario se renderiza con `st.markdown(html,
  unsafe_allow_html=True)` para tener control fino sobre colores por asignatura
  (paleta de 10). Sin dependencias adicionales tipo `streamlit-aggrid`.
- **Single-user**: la UI asume un solo alumno por instancia (mismo `data/cache.json`
  compartido). Multi-user requeriría un cache por sesión, fuera del scope V1.
- **Cierre de sesión**: limpia `session_state` y vuelve a la pantalla de login.

### Modo fallback: cuando las HARD del alumno dejan sin horarios

Cuando el alumno configura HARD imposibles de cumplir (por ejemplo, marca
todos los días como obligatoriamente libres, o pone `hora_max = "10:00"`
sobre una prematrícula con clases nocturnas), un solo pase del GA devolvería
lista vacía y el usuario vería una pantalla en blanco sin diagnóstico.

Para evitar esto, `_correr_ga` (`app.py`) implementa un **fallback en dos
pasos**:

1. **Primer pase**: corre el GA con el `ContextoAlumno` original respetando
   TODAS las HARD (las 4 intrínsecas + las 2 configurables por el alumno).
2. **Si el top queda vacío Y el alumno tiene HARD configurables activas**
   (`dias_libres_obligatorios != []`, `hora_min != None` o `hora_max !=
   None`), se corre un segundo pase con esas HARD **relajadas** (helper
   `_relajar_prefs` clona el `PreferenciasHorario` limpiando solo esos 3
   campos, preservando las SOFT).
3. Los cromosomas del segundo pase se marcan como **modo fallback** en
   `session_state.modo_fallback = True` y la UI muestra:
   - **Banner `st.warning`** arriba explicando qué HARD se relajaron.
   - **Grilla con bloques violadores marcados**: cada `BloqueHorario` que
     viola una HARD original se pinta con borde rojo grueso (3px) mediante
     la clase CSS `.horario td.clase.violada` (`box-shadow inset`), sin
     perder el color pastel de la asignatura. Ícono ⚠ en la esquina de la
     celda. Tooltip enriquecido con el motivo.
   - **Expander de recomendaciones** por horario: lista las secciones que
     tienen bloques violadores, con el motivo por bloque, para que el
     alumno sepa qué HARD quitar para poder tomarlas.
4. **Si el segundo pase también queda vacío** (o no había HARD configurables
   para relajar), se cae a la rama de **problema estructural**: `st.error`
   explicando que probablemente hay choques inevitables, prerequisitos no
   cumplidos, créditos excedidos o asignaturas sin sección disponible.
5. Nuevo flag `session_state.ga_ya_corrio` distingue entre "el alumno no
   apretó el botón todavía" (info azul "apretá el botón") y "el alumno
   apretó y no hubo resultados" (error rojo estructural). Antes ambos casos
   mostraban el mismo mensaje.

**Detección per-bloque**: el helper `_violaciones_bloque(bloque, prefs)`
replica la lógica de `verificar_dias_libres_obligatorios` y
`verificar_rango_horario` (fitness/hard_constraints.py) pero granular a un
único `BloqueHorario`, permitiendo marcar solo la celda que viola sin
descalificar todo el horario.

**Costo**: el segundo pase duplica el tiempo del GA (~0.5s total en el peor
caso). Solo se dispara cuando el primer intento fracasa por HARD
configurables, no en el flujo normal.

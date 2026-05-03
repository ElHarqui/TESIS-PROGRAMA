# Contexto del Proyecto: Tesis Programa - Scheduler de Horarios UNMSM

## Propósito general
Este proyecto es un sistema de scheduling automático para la Universidad Nacional Mayor de San Marcos (UNMSM). Usa datos de la plataforma SUM y modela la generación de horarios como un problema de optimización basado en algoritmos genéticos.

## Arquitectura general
La aplicación está organizada en capas con responsabilidades claras:

- Capa de datos (`data/`): adquiere información desde SUM y la transforma en objetos del dominio.
- Capa de dominio (`models/`): define los modelos de datos centrales (`BloqueHorario`, `Seccion`, `Cromosoma`).
- Capa de algoritmo genético (`genetic/`): genera la población inicial, cruza y muta soluciones, y ejecuta el bucle evolutivo.
- Capa de evaluación (`fitness/`): valida soluciones mediante restricciones duras y puntúa preferencias suaves.
- Capa de salida (`output/`): exporta o visualiza el resultado final.

La ruta principal de ejecución es `main.py`, que orquesta el scraping, parsing y (eventualmente) la optimización.

## Estructura del proyecto

### Archivos de entrada y ejecución
- `main.py`
  - Punto de entrada principal.
  - Carga variables de entorno `LOGIN` y `PASSWORD` desde `.env`.
  - Llama a `data.obtener_datos_sum()` para obtener los datos desde SUM.
  - Convierte la respuesta en objetos `Seccion` con `data.parsear_respuesta()`.
  - Imprime un listado básico de secciones y sus bloques.

### Paquete `data/`
Encargado de obtener y transformar datos de la plataforma SUM.

- `data/scraper.py`
  - Automatiza el login en `https://sum.unmsm.edu.pe/alumnoWebSum/login` usando Playwright.
  - Navega hasta la API interna de programación de asignaturas y la consulta con `fetch` desde la sesión autenticada.
  - Retorna JSON con la programación obtenida.

- `data/parser.py`
  - Convierte el JSON crudo en objetos de dominio.
  - `parsear_seccion(raw)` crea un `Seccion` y su lista de `BloqueHorario`.
  - `parsear_respuesta(data)` detecta la estructura del JSON y devuelve una lista de `Seccion`.

- `data/cache.py`
  - Implementa un caché sencillo con archivo JSON local y TTL de 1 hora.
  - Métodos: `get(key)` y `set(key, value)`.
  - Actualmente no limpia entradas expiradas.

- `data/__init__.py`
  - Exporta `obtener_datos_sum`, `parsear_seccion`, `parsear_respuesta` y `Cache`.

### Paquete `models/`
Modelos de dominio del problema de scheduling.

- `models/bloque.py`
  - `BloqueHorario` define un bloque de clase con:
    - `codAsignatura`, `codSeccion`, `codDocente`, `horario`, `dia`, `horaInicio`, `horaFin`, `codAula`, `tipo`, `desTipo`.
  - Incluye utilidades:
    - `hora_inicio_int` y `hora_fin_int` para convertir tiempos a minutos.
    - `choca_con(otro)` para detectar choque horario entre bloques.

- `models/seccion.py`
  - `Seccion` representa una sección de asignatura.
  - Campos clave: `ciclo`, `codAsignatura`, `desAsignatura`, `creditos`, `codSeccion`, `codDocente`, `nomDocente`, `apePatDocente`, `apeMatDocente`, `topeAlumnos`, `matriculados`, `bloques`.
  - Propiedades:
    - `docente_completo`: nombre completo del docente.
    - `disponibilidad`: porcentaje de cupos libres.

- `models/cromosoma.py`
  - `Cromosoma` representa un horario completo como lista de `Seccion`.
  - Actualmente solo contiene inicialización; falta lógica de evaluación interna.

- `models/__init__.py`
  - Exporta `BloqueHorario`, `Seccion` y `Cromosoma`.

### Paquete `genetic/`
Implementación del motor de algoritmo genético.

- `genetic/population.py`
  - `generar_poblacion_inicial(secciones_disponibles, tamano_poblacion)`.
  - TODO: implementar generación de cromosomas aleatorios.

- `genetic/operators.py`
  - `cruce(padre1, padre2)`.
  - `mutacion(cromosoma)`.
  - TODO: implementar operadores genéticos.

- `genetic/ga_engine.py`
  - `ejecutar_ga(poblacion_inicial, max_generaciones)`.
  - TODO: implementar el bucle principal de evolución.

### Paquete `fitness/`
Valora y valida cada horario candidato.

- `fitness/hard_constraints.py`
  - Verificaciones obligatorias:
    - `verificar_choques(cromosoma)`.
    - `verificar_cupos(cromosoma)`.
    - `verificar_prerequisitos(cromosoma)`.
  - Todas están definidas pero no implementadas.

- `fitness/soft_constraints.py`
  - Cálculo de preferencias:
    - `preferencia_horarios(cromosoma)`.
    - `preferencia_docentes(cromosoma)`.
  - Ambas son TODO.

- `fitness/evaluator.py`
  - `evaluar_fitness(cromosoma)` combina hard + soft.
  - Devuelve `0.0` si algún hard constraint falla.
  - Si pasa, pondera `score_horarios` y `score_docentes` con 70/30.

### Paquete `output/`
Generación de resultados legibles.

- `output/exporter.py`
  - `exportar_excel(cromosoma, filename)`.
  - `exportar_pdf(cromosoma, filename)`.
  - TODO: no están implementados.

- `output/visualizer.py`
  - `visualizar_grilla(cromosoma)`.
  - TODO: no está implementado.

## Resumen del contenido actual de cada archivo
Esta sección lista qué hace cada archivo hoy y cuánto está implementado.

- `main.py`
  - Contenido actual: arranca la app, carga credenciales, invoca scraping y parsing, y muestra secciones en consola.
  - Estado: implementado.

- `data/scraper.py`
  - Contenido actual: login Playwright, navegación al dashboard, fetch de API, retorna JSON.
  - Estado: implementado.

- `data/parser.py`
  - Contenido actual: transforma JSON en `Seccion` y `BloqueHorario`.
  - Estado: implementado.

- `data/cache.py`
  - Contenido actual: cache local JSON con TTL, `get` y `set`.
  - Estado: parcialmente implementado; falta limpieza de expirados y uso en `main.py`.

- `data/__init__.py`
  - Contenido actual: exporta funciones del paquete.
  - Estado: implementado.

- `models/bloque.py`
  - Contenido actual: clase `BloqueHorario` con detección de choques horarios.
  - Estado: implementado.

- `models/seccion.py`
  - Contenido actual: clase `Seccion` con propiedades de disponibilidad y nombre de docente.
  - Estado: implementado.

- `models/cromosoma.py`
  - Contenido actual: clase `Cromosoma` simple que guarda secciones.
  - Estado: esqueleto; falta lógica de fitness y validaciones.

- `models/__init__.py`
  - Contenido actual: exporta modelos.
  - Estado: implementado.

- `genetic/population.py`
  - Contenido actual: definición de función para generar población inicial.
  - Estado: TODO completo.

- `genetic/operators.py`
  - Contenido actual: definición de `cruce` y `mutacion`.
  - Estado: TODO completo.

- `genetic/ga_engine.py`
  - Contenido actual: firma de `ejecutar_ga` sin cuerpo.
  - Estado: TODO completo.

- `fitness/hard_constraints.py`
  - Contenido actual: firmas de verificaciones de choques, cupos y prerequisitos.
  - Estado: TODO completo.

- `fitness/soft_constraints.py`
  - Contenido actual: firmas de funciones de preferencia.
  - Estado: TODO completo.

- `fitness/evaluator.py`
  - Contenido actual: combina hard/soft score y penaliza con `0.0` si falla hard.
  - Estado: parcialmente implementado; falta integración con GA.

- `output/exporter.py`
  - Contenido actual: firmas de exportación a Excel/PDF.
  - Estado: TODO completo.

- `output/visualizer.py`
  - Contenido actual: firma para mostrar una grilla semanal.
  - Estado: TODO completo.

## Flujo de datos esperado

1. `main.py` arranca el proceso.
2. `data/scraper.py` obtiene los datos desde SUM.
3. `data/parser.py` convierte el JSON en `Seccion` y `BloqueHorario`.
4. `genetic/population.py` debe generar la población inicial de horarios (`Cromosoma`).
5. `genetic/ga_engine.py` aplica selección, cruce y mutación.
6. `fitness/evaluator.py` puntúa cada `Cromosoma`.
7. `output/exporter.py` / `output/visualizer.py` exportan o muestran el resultado.

## Dependencias
- `playwright==1.40.0`
- `python-dotenv==1.0.0`

## Estado actual del proyecto

- ✅ `data/` está parcialmente implementado: scraping y parsing funcionan.
- ✅ `models/` tiene la mayoría de los modelos de dominio.
- ⚠️ `genetic/` está esqueleto: falta implementar la lógica de GA.
- ⚠️ `fitness/` está en blanco: las reglas de validación/score aún no están codificadas.
- ⚠️ `output/` está en blanco: no genera archivos ni visuales.

## Puntos clave para escalar

- Implementar generación de población y operadores genéticos.
- Definir y codificar los constraints hard/soft.
- Integrar `evaluar_fitness()` dentro de `ejecutar_ga()`.
- Añadir exportación a Excel/PDF y visualización de grilla.
- Posible mejora: usar `data/cache.py` para evitar repetir requests a SUM.

## Nota para Claude

Este proyecto combina web scraping con optimización por algoritmo genético. El objetivo es construir un sistema de horarios que:
- no choque en horas,
- respete cupos,
- favorezca horarios y docentes preferidos,
- y pueda exportar el resultado.

La mayor parte de la estructura ya está definida, pero muchas funciones centrales aún son TODOs.

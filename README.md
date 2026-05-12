# Tesis Programa - Optimización de Matrícula con Algoritmo Genético

Este proyecto es parte de una tesis que desarrolla un sistema de optimización para la matrícula de asignaturas en la Universidad Nacional Mayor de San Marcos (UNMSM). Utiliza un scraper automatizado para extraer datos del Sistema de Matrícula (SUM) y un algoritmo genético para generar horarios óptimos considerando restricciones duras y suaves.

## Descripción

El sistema realiza las siguientes funciones:
- **Scraping automatizado**: Extracción de datos del SUM usando Playwright
- **Parseo de datos**: Conversión de datos crudos en estructuras Python
- **Optimización genética**: Generación de horarios óptimos usando algoritmos genéticos
- **Evaluación de fitness**: Cálculo de puntuaciones basado en restricciones
- **Visualización y exportación**: Salida de resultados en formatos útiles

## Características

- **Automatización completa**: Desde login hasta extracción y optimización
- **Modelado de datos**: Uso de dataclasses para representar secciones, horarios y cromosomas
- **Algoritmo genético**: Optimización con selección, cruce y mutación
- **Restricciones**: Manejo de restricciones duras (conflictos) y suaves (preferencias)
- **Configuración segura**: Credenciales en archivo `.env`
- **Salida estructurada**: Resultados listos para análisis

## Instalación

1. Clona el repositorio:
   ```bash
   git clone <url-del-repositorio>
   cd tesis-programa
   ```

2. Configura el entorno virtual (recomendado):
   ```bash
   python -m venv .venv
   # En Windows:
   .venv\Scripts\activate
   # En Linux/Mac:
   source .venv/bin/activate
   ```

3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

   Esto instalará:
   - `playwright==1.40.0`: Para automatización web
   - `python-dotenv==1.0.0`: Para variables de entorno

4. Instala los navegadores de Playwright:
   ```bash
   playwright install
   ```

## Configuración

1. Crea un archivo `.env` en la raíz del proyecto con tus credenciales del SUM:
   ```
   LOGIN=tu_codigo_unmsm@unmsm.edu.pe
   PASSWORD=tu_contraseña
   ```

2. Asegúrate de que las credenciales sean válidas para acceder al portal del SUM.

## Uso

### Ejecutar el programa completo

Ejecuta el script principal para scraping y optimización:
```bash
python main.py
```

El programa:
1. Verificará la caché de datos
2. Realizará scraping si es necesario (login automático en SUM)
3. Parseará los datos obtenidos
4. Ejecutará el algoritmo genético para generar horarios óptimos
5. Mostrará resultados y estadísticas

### Archivos principales

- `main.py`: Script principal que coordina todo el proceso
- `data/scraper.py`: Módulo de scraping con Playwright
- `genetic/ga_engine.py`: Motor del algoritmo genético
- `fitness/evaluator.py`: Evaluación de restricciones y fitness
- `models/`: Definiciones de dataclasses (Seccion, BloqueHorario, etc.)
- `output/`: Módulos para visualización y exportación

## Estructura del proyecto

```
tesis-programa/
├── main.py                 # Punto de entrada principal
├── requirements.txt        # Dependencias Python
├── .env                    # Configuración (credenciales)
├── data/                   # Módulos de datos
│   ├── scraper.py         # Scraping del SUM
│   ├── parser.py          # Parseo de respuestas
│   └── cache.py           # Sistema de caché
├── genetic/                # Algoritmo genético
│   ├── ga_engine.py       # Motor principal GA
│   ├── population.py      # Gestión de población
│   ├── operators.py       # Operadores (cruce, mutación)
│   └── selection.py       # Métodos de selección
├── fitness/                # Evaluación de fitness
│   ├── evaluator.py       # Evaluador principal
│   ├── hard_constraints.py # Restricciones duras
│   └── soft_constraints.py # Restricciones suaves
├── models/                 # Modelos de datos
│   ├── bloque.py          # BloqueHorario
│   ├── seccion.py         # Seccion
│   └── cromosoma.py       # Cromosoma GA
└── output/                 # Salida y visualización
    ├── exporter.py        # Exportación de resultados
    └── visualizer.py      # Visualización
```

## Dependencias

- **playwright**: Automatización web para scraping
- **python-dotenv**: Carga de variables de entorno
- **asyncio**: Operaciones asíncronas (Python 3.7+)
- **dataclasses**: Modelado de datos (Python 3.7+)
- **typing**: Type hints (Python 3.5+)
- **random**: Generación aleatoria (incluido en Python)

## Estructura de datos

### Seccion
- `ciclo`: Ciclo académico
- `codAsignatura`: Código de asignatura
- `desAsignatura`: Nombre de asignatura
- `creditos`: Créditos
- `codSeccion`: Número de sección
- `docente_completo`: Nombre del docente
- `topeAlumnos`: Capacidad máxima
- `matriculados`: Alumnos inscritos
- `disponibilidad`: % cupos libres
- `bloques`: Lista de BloqueHorario

### BloqueHorario
- `dia`: Día de la semana
- `horaInicio`/`horaFin`: Horarios (HH:MM)
- `codAula`: Código del aula
- `tipo`/`desTipo`: Tipo de horario
- `choca_con()`: Método para detectar conflictos

### Cromosoma
- Representa un horario candidato en el GA
- Contiene lista de secciones seleccionadas
- Métodos para evaluación de fitness

## Notas de desarrollo

- El proyecto usa Python 3.7+ por requerimientos de asyncio y dataclasses
- El scraping respeta las políticas del SUM y requiere credenciales válidas
- La optimización genética puede ajustarse modificando parámetros en `genetic/ga_engine.py`
- Los resultados se almacenan en caché para evitar scraping repetido

- El script usa `headless=False` por defecto para depuración visual
- Incluye manejo de modales de confirmación
- Esperas dinámicas para carga de páginas
- Fetch directo desde el navegador autenticado para evitar cookies manuales

## Licencia

Este proyecto es parte de una tesis académica. Consulta con el autor para uso comercial.

## Autor

Sebastian Leonardo Peralta Silvano 22200033 - Tesis UNMSM
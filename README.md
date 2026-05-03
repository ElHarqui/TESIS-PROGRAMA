# Tesis Programa - Scraper SUM UNMSM

Este proyecto es parte de una tesis que desarrolla un scraper automatizado para extraer la programación de asignaturas del Sistema de Matrícula (SUM) de la Universidad Nacional Mayor de San Marcos (UNMSM). Utiliza Playwright para automatizar el proceso de login y obtener datos de la API interna.

## Descripción

El scraper realiza las siguientes funciones:
- Autenticación automática en el portal del SUM usando credenciales de estudiante
- Extracción de la programación completa de asignaturas disponibles para matrícula
- Parseo de datos en estructuras de datos Python (dataclasses) para fácil manipulación
- Cálculo de disponibilidad de cupos y detección de conflictos horarios

## Características

- **Automatización completa**: Desde login hasta extracción de datos
- **Modelado de datos**: Uso de dataclasses para representar secciones, horarios y docentes
- **Detección de conflictos**: Método para verificar si dos bloques horarios se superponen
- **Configuración segura**: Credenciales almacenadas en archivo `.env`
- **Salida estructurada**: Datos parseados listos para análisis posterior

## Instalación

1. Clona el repositorio:
   ```bash
   git clone <url-del-repositorio>
   cd tesis-programa
   ```

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

   O instala manualmente:
   ```bash
   pip install playwright python-dotenv
   playwright install
   ```

## Configuración

1. Crea un archivo `.env` en la raíz del proyecto:
   ```
   LOGIN=tu_codigo_unmsm@unmsm.edu.pe
   PASSWORD=tu_contraseña
   ```

2. Asegúrate de que las credenciales sean válidas para el portal del SUM.

## Uso

Ejecuta el script principal:
```bash
python Prototipo.py
```

El programa:
1. Abrirá un navegador (visible por defecto)
2. Iniciará sesión en el SUM
3. Esperará el dashboard
4. Consultará la API de programación
5. Mostrará todas las secciones disponibles con detalles

### Archivos del proyecto

- `Prototipo.py`: Script principal con toda la lógica
- `Test.py`, `Test2.py`, `Test3.py`: Versiones anteriores o pruebas
- `.env`: Archivo de configuración (no subir a git)

## Dependencias

- `playwright`: Para automatización web
- `python-dotenv`: Para cargar variables de entorno
- `asyncio`: Para operaciones asíncronas (incluido en Python 3.7+)
- `dataclasses`: Para modelado de datos (incluido en Python 3.7+)
- `typing`: Para type hints (incluido en Python 3.5+)

## Estructura de datos

### Seccion
- `ciclo`: Número del ciclo académico
- `codAsignatura`: Código de la asignatura
- `desAsignatura`: Descripción de la asignatura
- `creditos`: Créditos de la asignatura
- `codSeccion`: Número de sección
- `docente_completo`: Nombre completo del docente
- `topeAlumnos`: Capacidad máxima
- `matriculados`: Alumnos inscritos
- `disponibilidad`: Porcentaje de cupos libres
- `bloques`: Lista de BloqueHorario

### BloqueHorario
- `dia`: Día de la semana
- `horaInicio`/`horaFin`: Horarios en formato HH:MM
- `codAula`: Código del aula
- `tipo`/`desTipo`: Tipo de horario (teoría, práctica, etc.)
- `choca_con()`: Método para detectar conflictos con otro bloque

## Notas de desarrollo

- El script usa `headless=False` por defecto para depuración visual
- Incluye manejo de modales de confirmación
- Esperas dinámicas para carga de páginas
- Fetch directo desde el navegador autenticado para evitar cookies manuales

## Licencia

Este proyecto es parte de una tesis académica. Consulta con el autor para uso comercial.

## Autor

Sebastian Leonardo Peralta Silvano 22200033 - Tesis UNMSM
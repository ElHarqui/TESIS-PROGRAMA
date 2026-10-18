<!--
  Informe Final — versión Markdown editable
  Fuentes: "Informe Final (1).docx" + capítulos LaTeX (chapters/*.tex)
           + estado real del programa (CONTEXTO_AVANCE.md, D:\WORKSPACE\TESIS PROGRAMA).
  El TEXTO es fiel a las fuentes; se limpió el formato y se integraron
  las tablas, figuras y features más recientes del prototipo.

  FUENTE DE LA VERDAD: los .tex (chapters/*.tex). Este markdown es un ESPEJO
  fiel de esos capítulos y se convierte al docx que se entrega al profesor.
  Todo cambio se hace primero en el LaTeX y luego se refleja aquí.

  NOTA: las figuras apuntan a ../imagenes/ (se ven en la vista previa de VSCode).
-->

**UNIVERSIDAD NACIONAL MAYOR DE SAN MARCOS**

*(Universidad del Perú, Decana de América)*

**FACULTAD DE INGENIERÍA DE SISTEMAS E INFORMÁTICA**

**Escuela Profesional de Ingeniería de Sistemas**

> **Diseño de un planificador automático de horarios académicos basado en algoritmos genéticos**

**PROYECTO DE TESIS**

- **AUTOR:** Sebastian Leonardo Peralta Silvano
- **ASESOR:** Cesar Luza Montero

Lima – Perú, 2025

---

## ÍNDICE

- [I. PLANTEAMIENTO DEL PROBLEMA](#i-planteamiento-del-problema)
  - [1.1 Descripción de la Realidad Problemática](#11-descripción-de-la-realidad-problemática)
  - [1.2 Formulación del problema](#12-formulación-del-problema)
  - [1.3 Objetivos](#13-objetivos)
  - [1.4 Justificación de la Investigación](#14-justificación-de-la-investigación)
  - [1.5 Alcance](#15-alcance)
- [II. MARCO TEÓRICO CONCEPTUAL](#ii-marco-teórico-conceptual)
- [III. REVISIÓN DE LITERATURA / ESTADO DEL ARTE](#iii-revisión-de-literatura--estado-del-arte)
- [IV. APORTE](#iv-aporte)
- [V. VALIDACIÓN](#v-validación)
- [VI. CONCLUSIONES](#vi-conclusiones)
- [VII. RECOMENDACIONES](#vii-recomendaciones)
- [REFERENCIAS](#referencias)

---

# I. PLANTEAMIENTO DEL PROBLEMA

## 1.1 Descripción de la Realidad Problemática

En el contexto actual de la educación superior, la gestión eficiente de los procesos académicos es fundamental para garantizar el bienestar y el éxito de la comunidad estudiantil. En la Universidad Nacional Mayor de San Marcos (UNMSM), el proceso de matrícula semestral, regulado por el Reglamento General de Matrícula para Pregrado (Universidad Nacional Mayor de San Marcos [UNMSM], 2023), exige que los estudiantes estructuren y definan su carga académica en un periodo de tiempo sumamente acotado y bajo un esquema de turnos escalonados basados en el promedio ponderado del alumno.

Si bien la infraestructura tecnológica actual (el Sistema Único de Matrícula o SUM) permite el registro de los cursos por turnos, la fase de planificación de horarios recae enteramente en el estudiante, careciendo de mecanismos institucionales de validación inteligente y optimización asistida. Históricamente, las iniciativas de investigación y desarrollo tecnológico en la propia facultad (Cortez et al., 2010; Ramos Milla, 2012; Blaz Aristo, 2016) se concentraron de forma exclusiva en la problemática administrativa centralizada —es decir, en asignar aulas físicas y balancear la carga docente para las autoridades académicas—, dejando desatendida la experiencia operativa del estudiante. Actualmente, los alumnos deben planificar sus horarios de manera empírica y manual, cruzando iterativamente la disponibilidad de cursos, verificando choques de horarios, validando los prerrequisitos de su plan de estudios y cuadrando sus tiempos personales.

Este proceso de "prueba y error" implica un alto esfuerzo cognitivo y propende a la generación de horarios subóptimos. Además, el sistema de matrícula por turnos según el promedio ponderado genera un nivel de incertidumbre crítico: cuando a un estudiante le corresponde matricularse, ciertas secciones ya presentan alta ocupación o saturación por alumnos de turnos anteriores. Depender de un único horario planificado manualmente resulta altamente ineficiente, ya que el estudiante debe improvisar modificaciones en tiempo real si encuentra cupos llenos, lo cual eleva los niveles de estrés, resulta en rechazos del sistema o en la creación de agendas académicas con intervalos excesivos ("huecos").

![Diagrama de Ishikawa: análisis causa–efecto de la problemática en la planificación manual de horarios durante la matrícula en la UNMSM.](../imagenes/ishikawa_problema.png)

Ante esta problemática, el empleo de Algoritmos Genéticos (AG) surge como una solución tecnológica robusta para abordar este desafío, conocido formalmente como el *University Course Timetabling Problem* (UCTP), un problema de optimización combinatoria clasificado como NP-Hard (Chen, Sze et al., 2021; Lewis, 2008). La adaptación de estos enfoques evolutivos permite procesar múltiples restricciones simultáneamente, estructuradas bajo la taxonomía de restricciones de Coello Coello (2002) y los criterios de dominancia de Deb (2000), distinguiendo entre *Hard Constraints* (inviolables, como cruces de horario, límite de créditos y prerrequisitos) y *Soft Constraints* (preferencias del usuario, como afinidad docente, turnos, días libres y la disponibilidad de cupos). Particularmente, la implementación de un motor genético que no solo busque el óptimo global, sino que extraiga un conjunto diverso de múltiples alternativas viables (Top-K) mediante técnicas de nichos fenotípicos y Distancia de Hamming (Hamming, 1950; Mahfoud, 1995; Yan y Deng, 2025), ofrece al estudiante de la UNMSM un abanico de 5 opciones pre-validadas que mitigan el impacto de la saturación de vacantes durante su turno de matrícula.

![Árbol de problemas: causas y efectos de la planificación manual del horario académico durante la matrícula.](../imagenes/arbol_de_problemas.png)

## 1.2 Formulación del problema

### 1.2.1 Problema General

¿En qué medida la implementación de un sistema de asistencia planificador automático de horarios, basado en algoritmos genéticos, mejora la calidad de la estructuración del horario académico y el nivel de satisfacción del estudiante durante el proceso de matrícula en la Universidad Nacional Mayor de San Marcos?

### 1.2.2 Problemas Específicos

1. ¿Cómo influye el empleo de un Algoritmo Genético en la reducción a cero de los conflictos de horarios y validaciones académicas (restricciones duras) durante la fase de planificación del estudiante, en comparación con la selección manual tradicional?

2. ¿De qué manera la evaluación de la función de aptitud (*fitness*) orientada a restricciones blandas (preferencias de turno, docentes y disponibilidad de cupos) optimiza la calidad de los horarios generados, permitiendo extraer un conjunto diverso de opciones viables (Top-K)?

3. ¿Cómo afecta el uso del prototipo propuesto a la Percepción de Utilidad y Facilidad de Uso (dimensiones evaluadas por el Modelo de Aceptación Tecnológica - TAM) por parte del estudiante de la UNMSM, en contraste con la experiencia actual?

## 1.3 Objetivos

### 1.3.1 Objetivo General

Determinar en qué medida la implementación de un prototipo de sistema de asistencia planificador automático de horarios, basado en algoritmos genéticos, mejora la calidad de la estructuración del horario académico y el nivel de satisfacción del estudiante durante el proceso de matrícula en la Universidad Nacional Mayor de San Marcos.

### 1.3.2 Objetivos Específicos

1. Diseñar e implementar un motor de recomendación de horarios utilizando Algoritmos Genéticos capaz de garantizar el cumplimiento estricto de las restricciones duras (cero choques de horario, validación de créditos máximos y aprobación de prerrequisitos).

2. Optimizar el cumplimiento de las restricciones blandas evaluando la función de aptitud (*fitness*), para extraer un conjunto de múltiples horarios de alta calidad y genéticamente diversos (Top-K) que ofrezcan contingencia ante la saturación de cupos del sistema por turnos.

3. Medir y analizar el nivel de satisfacción del estudiante respecto al uso del planificador automático propuesto, aplicando el instrumento validado del Modelo de Aceptación Tecnológica (TAM) para evaluar cuantitativamente la utilidad y facilidad de uso percibidas.

## 1.4 Justificación de la Investigación

### 1.4.1 Justificación Teórica

Esta investigación constituye una contribución significativa al acervo de conocimiento científico en el campo de la Ingeniería de Sistemas e Informática al abordar el *University Course Timetabling Problem* (UCTP) desde una perspectiva centrada en el estudiante y adaptada a la normativa universitaria local (Mahlous y Mahlous, 2023). Se valida la aplicabilidad de los Algoritmos Genéticos (Maspiyanti et al., 2025) combinados con esquemas de penalización progresiva continua basados en dominancia de restricciones (Deb, 2000; Coello Coello, 2002), no solo para la convergencia hacia soluciones libres de conflictos, sino para la extracción de conjuntos de soluciones genéticamente diversas (Top-K) mediante la Distancia de Hamming (Hamming, 1950) y métodos de nichos fenotípicos (Mahfoud, 1995) que respondan eficazmente a la incertidumbre de un entorno dinámico de asignación de vacantes.

### 1.4.2 Justificación Práctica

Desde una perspectiva pragmática, la solución propuesta aborda una problemática real y de alto impacto en la comunidad de la UNMSM: el enorme esfuerzo cognitivo y la ineficiencia que implica armar un horario manualmente frente al sistema de turnos por promedio ponderado. Al asistir al estudiante con un planificador que automatiza la extracción de datos (*web scraping*) y genera un ecosistema de 5 propuestas diversas de horario, validadas y optimizadas simultáneamente, se elimina el proceso empírico de "prueba y error". La implementación de este prototipo eleva la calidad del servicio educativo percibido y reduce drásticamente el estrés, asegurando que el alumno disponga de opciones sólidas al momento de ejercer su matrícula.

### 1.4.3 Justificación Metodológica

El estudio se distingue por su rigor metodológico al combinar una evaluación algorítmica técnica del software computacional con instrumentos de validación humana. Se emplearán métricas de rendimiento algorítmico de software puro, evaluando la tasa de convergencia del modelo genético y la métrica de distancia de diversidad entre cromosomas. Complementariamente, se aplicará el cuestionario estandarizado basado en el Modelo de Aceptación Tecnológica (TAM) postulado por Davis (1989) para medir objetivamente la usabilidad y aceptación del sistema propuesto.

## 1.5 Alcance

El desarrollo y validación del presente prototipo de sistema de asistencia para la planificación de horarios académicos se encuentra delimitado bajo criterios espaciales, temporales, tecnológicos y funcionales estrictos, los cuales garantizan la viabilidad operativa y el control experimental de la investigación.

- **Delimitación Espacial:** La investigación y el despliegue del caso de estudio se restringen exclusivamente a la Escuela Profesional de Ingeniería de Sistemas de la Facultad de Ingeniería de Sistemas e Informática (FISI) de la Universidad Nacional Mayor de San Marcos (UNMSM). Los datos de configuración de asignaturas, secciones, docentes e infraestructura horaria corresponden a la oferta académica real provista por dicha facultad.

- **Delimitación Temporal:** El portafolio de datos curriculares, la disponibilidad de vacantes y el procesamiento de la información corresponden de manera estricta al ciclo académico de matrícula 2026-I.

- **Delimitación Tecnológica:** El prototipo se encuentra desarrollado íntegramente sobre el lenguaje de programación Python en su versión 3.13. La automatización de la captura de datos utiliza la librería *Playwright* para la interacción asíncrona con el Sistema Único de Matrícula (SUM). La interfaz gráfica interactiva se despliega mediante el framework de aplicaciones web *Streamlit*, y el motor de salida ofimática genera artefactos en formatos estandarizados de Microsoft Excel (a través de *openpyxl*) y documentos PDF (empleando *reportlab*).

- **Delimitación Funcional:** La solución tecnológica está concebida exclusivamente como una herramienta de soporte a la decisión orientada al estudiante (usuario final). El sistema procesa los datos correspondientes a las asignaturas precargadas en el entorno de prematrícula del usuario, evalúa las restricciones duras del plan de estudios e historial académico del alumno, y optimiza la distribución horaria en función de sus preferencias subjetivas. El sistema tiene como límite la generación de un conjunto diversificado de exactamente cinco (5) alternativas de horarios óptimos (Top-K) con una distancia estructural mínima de una sección entre sí.

Se excluye explícitamente del alcance de esta tesis la automatización de transacciones financieras (pagos de derechos de matrícula), la gestión interna de reservas administrativas de aulas a nivel de toda la universidad, o la modificación directa de las bases de datos transaccionales del SUM, actuando el sistema únicamente como un agente externo de lectura, validación y recomendación optimizada. Asimismo, el módulo predictivo de vacantes (`prediccion/`) se mantiene en una fase de diseño arquitectónico aislado y fuera del *pipeline* principal de ejecución, operando el optimizador actual con los *snapshots* transaccionales de disponibilidad de cupos en tiempo real y cachés locales con tiempo de vida (TTL) controlado.

---

# II. MARCO TEÓRICO CONCEPTUAL

La presente investigación se fundamenta en un marco científico interdisciplinario que unifica las teorías de la optimización combinatoria, la computación evolutiva bioinspirada, el diseño de software arquitectónico y los modelos psicométricos de adopción tecnológica. Los pilares teóricos se estructuran detalladamente a continuación.

## El Problema de Programación de Horarios Universitarios (UCTP)

El *University Course Timetabling Problem* (UCTP) constituye un desafío clásico en el ámbito de la investigación de operaciones y las ciencias de la computación. Su naturaleza matemática consiste en asignar un conjunto finito de eventos académicos (clases, laboratorios, secciones de asignaturas) dentro de una grilla espacio-temporal preestablecida (franjas horarias y días de la semana), satisfaciendo simultáneamente múltiples requerimientos de carácter operativo (Chen, Sze et al., 2021; Lewis, 2008).

Desde la perspectiva de la teoría de la complejidad computacional, el UCTP está sólidamente clasificado dentro de la categoría de problemas NP-Hard (Herath, 2017). Esto implica que el tiempo necesario para hallar una solución óptima exacta mediante algoritmos deterministas o métodos de enumeración exhaustiva crece de manera exponencial en relación al tamaño de las variables de entrada (número de alumnos, cursos y secciones). Para una institución masiva, los enfoques matemáticos lineales rígidos resultan inviables en entornos de tiempo real, lo que justifica teórica y técnicamente la adopción de metaheurísticas estocásticas capaces de explorar grandes espacios de búsqueda y converger hacia soluciones cuasi-óptimas de alta calidad en tiempos de cómputo drásticamente reducidos (Chen, Sze et al., 2021; Mahlous y Mahlous, 2023).

## Algoritmos Genéticos Adaptativos (AGA) y Dinámica de Poblaciones

Los Algoritmos Genéticos representan una rama madura de la computación evolutiva inspirada en las mecánicas de la selección natural y la genética de poblaciones (Goldberg, 1989; Michalewicz, 1996). Operan sobre un conjunto de soluciones tentativas denominadas cromosomas, los cuales evolucionan iterativamente a través de generaciones mediante operadores de selección, recombinación (*crossover*) y mutación. En una arquitectura de AG de parámetros fijos, las tasas de mutación y cruce permanecen inmutables durante toda la ejecución, lo que induce un elevado riesgo de convergencia prematura, provocando que el algoritmo pierda diversidad y se estanque en óptimos locales deficientes.

Para resolver esta vulnerabilidad estructural, la teoría contemporánea fundamenta el uso de los Algoritmos Genéticos Adaptativos (AGA) (Yan y Deng, 2025). Estos sistemas evalúan continuamente la dispersión de la aptitud (*fitness*) y la entropía de la población para ajustar dinámicamente las probabilidades de los operadores. Cuando el sistema detecta homogeneidad en las soluciones, incrementa automáticamente la tasa de mutación para forzar la exploración de nuevas regiones del espacio de búsqueda; por el contrario, cuando la población muestra una adecuada diversidad, optimiza el cruce para explotar y refinar los bloques de construcción de alta calidad ya encontrados. 

Asimismo, la teoría de la computación evolutiva en problemas de satisfacción de restricciones (CSP) subraya el fenómeno de la **epistasia y disrupción de operadores** (Burke et al., 2004; Eiben y Smith, 2015; Michalewicz, 1996): en el UCTP, los genes (secciones de cursos) exhiben un alto grado de dependencia no lineal entre sí. La recombinación de dos progenitores factibles mediante cruce uniforme puede desarticular bloques constructores libres de solapamiento y generar descendientes infactibles con cruces horarios. Por esta razón, el diseño evolutivo debe articular esquemas de preservación de soluciones de élite con operadores de selección robustos e insensibles a distorsiones de escala. 

En este marco, la selección por torneo determinista (Blickle y Thiele, 1996) con tamaño $k=3$ ofrece una ventaja computacional determinante frente a la selección proporcional por ruleta clásica (Goldberg, 1989). Mientras que la ruleta colapsa ante valores de aptitud negativos y sufre por distorsiones de presión selectiva según la dispersión del *fitness*, la selección por torneo opera sobre comparaciones puramente ordinales basadas en rangos de dominancia ($\max(f_A, f_B)$). Esta propiedad garantiza invariancia estricta ante traslaciones de escala y permite guiar con naturalidad a la población desde el semieje de penalizaciones negativas continuas ($f < 0,0$) hacia la frontera factible ($f \in [0,0; 1,0]$) sin requerir transformaciones artificiales de escala (Deb, 2000).

![Flujo del ciclo evolutivo del Algoritmo Genético: inicialización de la población, evaluación de aptitud, selección, cruce, mutación e iteración hasta el criterio de convergencia.](../imagenes/flujo_genetico.png)

## Optimización Multi-objetivo y Taxonomía de Restricciones

La estructuración de horarios de matrícula no persigue un único fin absolutista, sino el equilibrio de múltiples objetivos en conflicto, requiriendo una formalización matemática precisa a través de una función de aptitud (*fitness function*) con pesos balanceados. Para tal fin, la teoría del modelado de restricciones clasifica las reglas del dominio en dos grandes familias (Chen, Sze et al., 2021; Coello Coello, 2002):

1. **Restricciones Duras (*Hard Constraints*):** Hacen referencia a condiciones físicas y normativas inviolables cuya transgresión descalifica de inmediato la factibilidad de la solución. En el contexto universitario, abarcan la no superposición temporal de bloques de una misma sección o de diferentes cursos matriculados (cero choques horarios, formalizado matemáticamente mediante el Álgebra de Intervalos de Allen, 1983), el respeto inflexible al límite máximo de créditos permitidos por periodo lectivo (24 créditos según la normativa local) y la validación curricular estricta de prerrequisitos aprobados mediante el análisis retrospectivo del historial académico del alumno. Mientras que los enfoques clásicos recurrían a la "pena de muerte" asignando arbitrariamente aptitud nula ($0,0$) y destruyendo el gradiente de búsqueda (Coello Coello, 2002), la teoría moderna de optimización evolutiva con restricciones establece el uso de **penalizaciones progresivas continuas** fundamentadas en la dominancia de restricciones (Deb, 2000). Bajo este principio, las soluciones infactibles se mapean al semieje estrictamente negativo ($f < 0,0$), preservando la presión de selección hacia la frontera factible.

2. **Restricciones Blandas (*Soft Constraints*):** Representan metas de conveniencia, preferencias individuales o factores cualitativos que no impiden la ejecución material del horario, pero que determinan su nivel de confort y aceptación por el estudiante. Su modelamiento se realiza mediante penalizaciones graduales en la función objetivo. Comprenden el ajuste al turno horario preferido (mañana, tarde o noche), la asignación de docentes con puntuaciones de alta afinidad cargadas por el usuario, la densidad de la agenda (preferencia por horarios compactos para reducir horas muertas o "huecos" frente a horarios distribuidos), y la disponibilidad porcentual de vacantes reales en el SUM, evaluada como una variable de viabilidad probabilística frente al sistema jerárquico de turnos de matrícula.

## Diversidad Estructural y Conjuntos Top-K

En la teoría clásica de optimización, el objetivo final es hallar e informar el cromosoma con el mayor puntaje de aptitud absoluta. No obstante, en un entorno dinámico y competitivo —donde las vacantes de las secciones se agotan en tiempo real según el turno escalonado por promedio ponderado del estudiante—, proveer un único horario óptimo introduce una alta fragilidad. Si una sección de ese horario único se satura minutos antes del turno del alumno, toda la estructura planificada colapsa.

La teoría de optimización multi-objetivo moderna plantea la extracción de conjuntos de soluciones diversas o sub-óptimas de alta calidad, conocidas como portafolios Top-K (Yan y Deng, 2025). Tras completar el ciclo de generaciones del algoritmo evolutivo, se aplica un mecanismo heurístico codicioso (*greedy*) encargado de seleccionar no a los individuos con los puntajes más altos secuenciales (los cuales suelen ser copias idénticas con variaciones triviales), sino a aquellos que preservan un rendimiento de *fitness* sobresaliente pero garantizan una separación estructural mínima fundamentada en la **Distancia de Hamming (Hamming, 1950)** y en las técnicas de nichos fenotípicos (*niching*) (**Mahfoud, 1995**), medida como la diferencia de al menos una sección académica entre alternativas ($d_H \ge 1$). Esto dota al estudiante de un abanico de contingencia real y pre-validada.

## Modelo de Aceptación Tecnológica (TAM)

La validación de una solución de ingeniería de sistemas orientada al usuario final no puede limitarse a la verificación del rendimiento computacional, sino que debe incorporar marcos teóricos que evalúen la interacción sociotécnica. El Modelo de Aceptación Tecnológica (TAM), desarrollado originalmente por Davis (1989), es el estándar científico de referencia para predecir y explicar la intención de adopción de un sistema de información. Postula que la aceptación de una tecnología está determinada causalmente por dos constructos perceptuales primarios:

- **Utilidad Percibida (*Perceived Usefulness* — PU):** El grado en que el sujeto considera que el uso del software mejorará su desempeño y optimizará la eficiencia en sus actividades (en este caso, lograr estructurar una carga académica óptima con cero conflictos y alta resiliencia ante turnos competitivos).

- **Facilidad de Uso Percibida (*Perceived Ease of Use* — PEOU):** El grado en que el usuario percibe que la interacción con el sistema estará libre de esfuerzo físico o mental excesivo. El TAM fundamenta la hipótesis metodológica de esta tesis: al desplazar el enorme esfuerzo cognitivo del cruce manual de horarios hacia un motor automático evolutivo con interfaz web usable, la PEOU incrementará de forma significativa, impactando positivamente en la satisfacción del alumnado.

![Modelo de Aceptación Tecnológica (TAM): relación entre la Utilidad Percibida (PU) y la Facilidad de Uso Percibida (PEOU) sobre la actitud e intención de uso del sistema (Davis, 1989).](../imagenes/modelo_tam.png)

---

# III. REVISIÓN DE LITERATURA / ESTADO DEL ARTE

La revisión exhaustiva de la literatura científica internacional y nacional evidencia un desarrollo sostenido en el abordaje algorítmico del problema de horarios académicos, marcando tendencias claras y exponiendo brechas metodológicas que justifican la contribución técnica de la presente tesis.

## Evolución de los Enfoques Evolutivos Aplicados al UCTP

A nivel global, la comunidad científica ha consolidado el uso de metaheurísticas poblacionales como la estrategia más robusta para resolver las instancias complejas del UCTP, reemplazando los modelos analíticos rígidos de las décadas precedentes. Los *surveys* internacionales de referencia, como el elaborado por Chen, Sze et al. (2021), demuestran que las técnicas basadas en Algoritmos Genéticos superan consistentemente a los métodos heurísticos locales simples al balancear de forma eficiente los mecanismos de exploración del espacio de búsqueda y explotación de soluciones locales.

La vanguardia científica para el periodo 2024–2025 se concentra en dotar de inteligencia dinámica a estos motores evolutivos. Investigaciones nucleares como las de Yan y Deng (2025) validan que los Algoritmos Genéticos Adaptativos (AGA) —que modifican dinámicamente sus tasas de variación en función de la homogeneidad intergeneracional— reducen drásticamente los tiempos de cómputo y alcanzan valores de aptitud óptimos frente a entornos caracterizados por la informatización educativa masiva y la personalización curricular. Asimismo, en el ámbito de la calendarización de clases, Chen, Yue et al. (2021) implementaron un algoritmo genético mejorado que optimiza la codificación y los operadores de cruce, demostrando que la especialización estructural del algoritmo sobre el dominio del problema acelera sustancialmente la eliminación de colisiones horarias frente a configuraciones genéticas canónicas.

![Línea de evolución de los enfoques de resolución del UCTP: de la optimización estática a los métodos adaptativos e híbridos.](../imagenes/linea_de_evolucion_de_enfoque.png)

## Operadores Híbridos e Inteligencia Computacional Intermedia

De forma complementaria al ajuste dinámico de los parámetros globales, la literatura especializada destaca el codiseño de operadores evolutivos que integran técnicas de hibridación inteligente. El estudio desarrollado por Maspiyanti et al. (2025) demuestra empíricamente que la combinación de Algoritmos Genéticos con controladores basados en Lógica Difusa (*Fuzzy Logic*) para guiar el proceso de recombinación genómica (*crossover*) resulta altamente eficiente. Al evaluar la calidad cualitativa de las soluciones parciales bajo reglas difusas antes de ejecutar el intercambio de genes, se acelera la convergencia y se reduce a cero el índice de colisiones horarias en menor número de generaciones, proporcionando la fundamentación teórica para el tratamiento diferenciado de las restricciones complejas dentro de la computación evolutiva.

## Antecedentes Nacionales y Locales en la Gestión de Horarios

En el ecosistema universitario peruano, la optimización de horarios mediante metaheurísticas posee precedentes significativos enfocados prioritariamente en la automatización de la carga institucional. En la Universidad Nacional Mayor de San Marcos, los trabajos pioneros de Naupari y Rosales (2010), formalizados posteriormente por Cortez et al. (2010) en la *Revista de Investigación de Sistemas e Informática* (RISI) de la FISI, sentaron las bases para el modelamiento de las restricciones de infraestructura física de la facultad. Desarrollaron un prototipo en C++/Visual Basic para una instancia de 54 asignaturas y más de 100 secciones, empleando un Algoritmo Genético canónico con selección por ruleta y penalizaciones estáticas. Si bien comprobaron la viabilidad de los AG en San Marcos, su modelo evidenció dificultades de convergencia por estancamiento prematuro y no contempló la perspectiva de las preferencias del alumno ni la dinámica de vacantes.

Posteriormente, Ramos Milla (2012) exploró en la misma facultad la técnica de Búsqueda Tabú (*Tabu Search*), implementando estructuras de memoria a corto plazo (*recency-based memory*) para evitar ciclos y memoria a largo plazo basada en frecuencia para guiar la asignación docente. Su contribución demostró que, aunque las heurísticas de trayectoria individual resuelven de forma eficiente escenarios con restricciones moderadas, presentan una marcada vulnerabilidad para quedar atrapadas en óptimos locales frente a espacios de búsqueda multimodales y fuertemente restringidos, confirmando la superioridad de los enfoques poblacionales basados en algoritmos genéticos.

En 2016, la investigación desarrollada por Blaz Aristo (2016) significó un hito local al diseñar un sistema inteligente basado en AG adaptado estrictamente a la normativa de pregrado de la UNMSM, demostrando una eficiencia sobresaliente en la distribución automática de la carga académica y en la eliminación total de errores humanos en la asignación docente de la facultad. No obstante, al igual que los trabajos precedentes, su implementación se restringió a matrices de datos estáticas para el decanato, sin conexión viva a las bases de datos transaccionales del SUM ni capacidad de entregar alternativas diversificadas para la toma de decisiones del estudiante.

En el ámbito interinstitucional nacional, destaca la investigación de Angeles Díaz (2015) en la Pontificia Universidad Católica del Perú (PUCP), quien implementó una arquitectura híbrida combinando la metaheurística constructiva GRASP (*Greedy Randomized Adaptive Search Procedure*) con Algoritmos Genéticos para la programación de horarios de la Sección de Ingeniería Informática. Dicho enfoque demostró la eficacia de emplear un operador constructivo voraz para inicializar la población con soluciones factibles; sin embargo, al estar concebido como un proceso centralizado por lotes para la dirección de carrera, requería tiempos de cómputo del orden de decenas de minutos, lo que imposibilita su uso interactivo por parte de los alumnos durante la matrícula. Asimismo, investigaciones aplicadas en otras instituciones del ámbito nacional (Guzmán y Eguía, 2018; Salvador, 2021) corroboran la eficacia y la viabilidad práctica de los enfoques bioinspirados para resolver el problema de *timetabling* bajo las condiciones y limitaciones operativas de la educación superior local.

**Cuadro comparativo de antecedentes frente a la propuesta de la presente tesis:**

| Autor (Año) | Técnica | Contexto | Resultado clave | TAM | Top-K |
|---|---|---|---|:---:|:---:|
| Maspiyanti et al. (2025) | AG + Lógica Difusa (cruce adaptativo) | U. Pancasila (Indonesia) | Cero conflictos en menos generaciones | No | No |
| Yan y Deng (2025) | AG Adaptativo (AGA) | Cursos de computación | Convergencia rápida, aptitud óptima | No | No |
| Mahlous y Mahlous (2023) | AG con operadores de reparación | Asignación a estudiantes | >90 % de preferencias satisfechas | No | No |
| Cortez et al. (2010) / Naupari y Rosales (2010) | AG estándar | FISI-UNMSM (Perú) | Sistema de apoyo viable para la facultad | No | No |
| Ramos Milla (2012) | Búsqueda Tabú (*Tabu Search*) | FISI-UNMSM (Perú) | Automatización web de carga docente | No | No |
| Angeles Díaz (2015) | Híbrido GRASP + AG | Informática, PUCP (Perú) | Distribución de horarios académicos | No | No |
| Blaz Aristo (2016) | AG estándar | FISI-UNMSM (Perú) | Cero violaciones de restricciones duras | No | No |
| Guzmán y Eguía (2018) | AG estándar | IES / UTP (Perú) | Horarios válidos en tiempos aceptables | No | No |
| **Propuesta (esta tesis)** | **AGA orientado al estudiante** | **EP Ing. Sistemas, FISI-UNMSM** | **Cero choques + portafolio diverso de 5 horarios validados** | **Sí** | **Sí** |

> *Nota:* TAM = validación de aceptación tecnológica; Top-K = extracción de múltiples horarios estructuralmente diversos.

## Brecha del Conocimiento

A pesar de la madurez técnica de los algoritmos evolutivos descritos en el Estado del Arte, el análisis crítico de la literatura científica revela una persistente brecha sociotécnica y operativa, particularmente visible en el contexto de las universidades públicas latinoamericanas:

1. **Monopolio del Enfoque Administrativo-Institucional:** La totalidad de los antecedentes locales y la gran mayoría de los internacionales (p. ej., Cortez et al., 2010; Naupari y Rosales, 2010; Ramos Milla, 2012; Angeles Díaz, 2015; Blaz Aristo, 2016; Guzmán y Eguía, 2018; Salvador, 2021) abordan el problema exclusivamente desde la perspectiva de la administración central de la universidad. Sus funciones objetivo están diseñadas para maximizar el uso físico de las aulas, balancear los contratos docentes y reducir costos operativos institucionales. Si bien investigaciones internacionales recientes como la de Mahlous y Mahlous (2023) demuestran el interés emergente por optimizar horarios según preferencias estudiantiles, carecen de articulación con la infraestructura de matrícula en tiempo real de universidades públicas peruanas. Existe una ausencia de herramientas metaheurísticas concebidas e implementadas desde y para el beneficio directo del estudiante de la UNMSM como usuario final e individual del sistema.

2. **Fragmentación Tecnológica y Entrada Manual de Datos:** Los sistemas existentes operan en entornos cerrados o de laboratorio. Requieren que los datos de entrada (cursos, secciones, aulas, prerrequisitos) sean digitados o cargados manualmente en matrices estáticas por un operador humano. No se documentan soluciones integradas *end-to-end* que conecten agentes automáticos de extracción de datos en tiempo real (*web scraping*) sobre sistemas académicos vivos con un motor de optimización evolutiva.

3. **Rigidez Estática ante Entornos Competitivos (Turnos):** Las soluciones precedentes asumen un entorno estático y se limitan a generar un único horario rígido definitivo. Este paradigma resulta ineficaz en instituciones como la UNMSM, donde la matrícula se rige por un sistema dinámico de turnos escalonados por mérito académico (promedio ponderado). Bajo esta normativa, las vacantes se agotan en tiempo real, lo que exige que el sistema no entregue una solución única, sino un portafolio de alternativas estructuralmente diversificadas (Top-K) que otorguen resiliencia y capacidad de contingencia inmediata al alumno al momento de su turno de inscripción.

4. **Omisión de la Validación Científica Humana (UX/TAM):** Las investigaciones previas evalúan el éxito de sus sistemas utilizando únicamente métricas de rendimiento computacional abstracto (tiempo de CPU, tasas de convergencia del *fitness* matemático). Se ignora por completo la medición psicométrica formal de la usabilidad, la utilidad percibida y el impacto directo en la reducción del estrés y la frustración del estudiante, omitiendo marcos validados internacionalmente como el modelo TAM (Davis, 1989).

## Aporte de la Tesis frente a la Brecha

La presente investigación mitiga directamente las brechas identificadas mediante el diseño, implementación y validación de una solución de software de optimización integral y centrada en el estudiante. El aporte específico de este trabajo se consolida en los siguientes componentes de ingeniería:

- Un flujo unificado y automatizado que realiza la extracción directa de datos académicos desde el SUM utilizando agentes de automatización web (*Playwright*), garantizando la fidelidad de los datos de programación curricular, prematrícula, prerrequisitos e historial académico sin intervención manual.

- Una representación cromosómica optimizada y parametrizada externamente mediante estructuras JSON compartidas (`config_ga.json`), permitiendo sintonizar los pesos de la función de aptitud para balancear dinámicamente las preferencias horarias, afinidades docentes y disponibilidad de vacantes.

- Un motor genético adaptativo que implementa un operador de extracción heurístico *greedy* de diversidad estructural, garantizando la entrega de un portafolio de exactamente 5 horarios viables y genéticamente diferenciados entre sí (Top-5 Diverso), otorgando al alumno un mecanismo robusto de resiliencia ante la pérdida de cupos en su turno de matrícula.

- Un marco de evaluación metodológico bidireccional que somete el prototipo a pruebas técnicas de convergencia algorítmica y, simultáneamente, convalida su impacto humano midiendo las dimensiones de usabilidad mediante el Modelo de Aceptación Tecnológica (TAM) (Davis, 1989).

## Conclusión del Estado del Arte

Las evidencias analizadas confirman que los Algoritmos Genéticos continúan siendo la técnica metaheurística más robusta y con mayor tasa de éxito para resolver las instancias complejas del UCTP en el ámbito universitario (Chen, Sze et al., 2021). Asimismo, la literatura confirma que para asegurar la aplicabilidad práctica de estos modelos matemáticos abstractos en entornos reales, es imperativo embeber las reglas normativas específicas de la institución dentro de los operadores del sistema y validar el resultado final cruzando la eficiencia algorítmica con la satisfacción humana. Esta tesis se posiciona estratégicamente en esa intersección, ofreciendo una solución de software replicable, metodológicamente rigurosa y alineada con las necesidades reales del alumnado de la UNMSM.

---

# IV. APORTE

## 4.1. Estudio de necesidades y Análisis de Requerimientos

El desarrollo del presente prototipo nace de la necesidad de mitigar el alto esfuerzo cognitivo, la ineficiencia operativa y la incertidumbre que experimentan los estudiantes de la Universidad Nacional Mayor de San Marcos (UNMSM) durante el proceso semestral de matrícula. La problemática central radica en la explosión combinatoria propia de la planificación horaria (selección coordinada entre múltiples asignaturas, secciones y bloques horarios dispersos), condicionada de manera determinante por el sistema normativo de matrícula por turnos escalonados según el promedio ponderado.

Para abordar esta problemática de forma integral, se formalizaron los siguientes requerimientos fundamentales de software:

**Requerimientos Funcionales:**

- **Extracción automatizada y resiliente:** El sistema debe autenticarse en el Sistema Único de Matrícula (SUM) y extraer en tiempo real la programación de horarios, prematrícula, plan de estudios curricular e historial académico del estudiante. El mecanismo debe implementar tolerancia a fallos, persistencia en caché local con tiempo de vida (TTL) y aislamiento entre usuarios.

- **Validación rigurosa de restricciones duras (*Hard Constraints*):** El sistema debe garantizar matemáticamente la ausencia de cruces de horarios, impedir la duplicidad de asignaturas, certificar el cumplimiento estricto de prerrequisitos académicos mediante validación 1-a-1 contra el historial del alumno y respetar el límite máximo normativo de créditos (24 créditos en el plan 2018, en estricta observancia del Reglamento General de Matrícula para Pregrado [UNMSM, 2023]).

- **Restricciones duras configurables por el usuario:** Permitir que el estudiante active de forma opcional restricciones rígidas personales, tales como días obligatoriamente libres (por motivos laborales o personales) y acotamiento de rangos horarios permitidos (hora mínima de inicio y hora máxima de salida).

- **Optimización multiobjetivo de preferencias (*Soft Constraints*):** La solución debe maximizar de manera simultánea las preferencias del estudiante (afinidad de turnos diurno, tarde o noche; días libres deseados; densidad compacta o distribuida; ponderación individual de docentes) y ponderar la disponibilidad real de cupos para favorecer secciones con menor probabilidad de saturación.

- **Extracción de portafolio diverso (Top-K):** El motor no debe limitarse a devolver un único horario óptimo, sino generar un conjunto de exactamente cinco (5) alternativas de horarios válidos que mantengan una separación estructural mínima de al menos una sección distinta entre sí (Distancia de Hamming $d_H \ge 1$, bajo técnicas de nichos fenotípicos de Mahfoud, 1995), incorporando deduplicación estricta para evitar variantes redundantes.

- **Modo de contingencia y diagnóstico (*Fallback Mode*):** En caso de que las restricciones duras configuradas por el estudiante hagan imposible encontrar una solución factible, el sistema debe relajar automáticamente las restricciones opcionales, conservar las restricciones académicas inviolables y alertar visualmente al usuario indicando el origen del conflicto y las recomendaciones de ajuste.

**Requerimientos No Funcionales:**

- **Rendimiento computacional:** Tiempos de ejecución subsegundo ($< 1 \text{ s}$) para el bucle evolutivo sobre el espacio de búsqueda real mediante optimización en memoria y estructuras de datos eficientes.
- **Usabilidad y adopción tecnológica:** Interfaz web interactiva centrada en el usuario, diseñada bajo los constructos del Modelo de Aceptación Tecnológica (TAM) de Davis (1989), que abstraiga la complejidad matemática del algoritmo mediante calendarios semanales matriciales, tarjetas de métricas analíticas e interfaces de comparación visual.
- **Portabilidad de salida:** Capacidad de exportación multiplataforma de las alternativas generadas hacia formatos ofimáticos estándar (Microsoft Excel multihaja y documentos PDF de alta fidelidad apaisados).

## 4.2. Diseño de la solución Tecnológica

Para garantizar una separación rigurosa de responsabilidades, alta cohesión y bajo acoplamiento (Bass et al., 2012), el sistema fue concebido bajo una **arquitectura de software en capas (*N-Tier Architecture*)** implementada en Python 3.13. El diseño modular se estructura en las siguientes capas lógicas:

1. **Capa de Datos (`data/`):**  
   Responsable de la adquisición, transformación y persistencia temporal de la información académica. Implementa un componente de automatización de navegador mediante la librería *Playwright* (`scraper.py`) que interactúa con los endpoints autenticados del SUM. Para garantizar alta eficiencia y evitar sobrecarga sobre los servidores universitarios, incorpora un subsistema de caché transaccional (`cache.py`) basado en archivos JSON locales con tiempo de vida (TTL) configurable y aislamiento de datos por identificador de usuario.

2. **Capa de Dominio (`models/`):**  
   Modela las entidades conceptuales del negocio mediante estructuras de datos inmutables (*dataclasses*). Destaca la clase `BloqueHorario`, la cual implementa la verificación de solapamientos temporales fundamentada en el **Álgebra de Intervalos de Allen (1983)** en una dimensión temporal discreta: dos bloques colisionan si y solo si pertenecen al mismo día de la semana y sus intervalos en minutos $[inicio_A, fin_A)$ y $[inicio_B, fin_B)$ presentan intersección no vacía ($inicio_A < fin_B \land inicio_B < fin_A$). Asimismo, se definen las entidades `Seccion` (con sus docentes, créditos y cupos), `Cromosoma` (representación vectorial de un horario) y `HorarioResultado` (entidad enriquecida con métricas de evaluación).

3. **Capa de Evaluación (*Fitness Engine*, `fitness/`):**  
   Encapsula las reglas de negocio en un objeto inmutable denominado `ContextoAlumno`, el cual consolida el plan de estudios, asignaturas aprobadas, límites de créditos, preferencias horarias, ponderación de docentes y pesos de optimización. Separa la lógica en dos subsistemas:
   - *Evaluador de Restricciones Duras (`hard_constraints.py`):* Computa una penalización progresiva continua según la gravedad y cantidad de infracciones.
   - *Evaluador de Restricciones Blandas (`soft_constraints.py`):* Calcula funciones de utilidad normalizadas en $[0,0; 1,0]$ para horarios, docentes y vacantes.

4. **Capa del Algoritmo Genético (`genetic/`):**  
   Contiene el motor evolutivo metaheurístico. Implementa la generación de la población inicial con exclusión de secciones no válidas (`population.py`), operadores de cruce uniforme por asignatura y mutación aleatoria con reemplazo de sección (`operators.py`), selección por torneo determinista basada en dominancia ordinal (Blickle y Thiele, 1996) en `selection.py`, loop generacional con elitismo diverso (`ga_engine.py`) y el selector greedy de nichos y preservación de diversidad fenotípica (Mahfoud, 1995) basado en la Distancia de Hamming (Hamming, 1950) para la extracción del portafolio Top-5 diverso (`top_k_diversos`).

5. **Capa de Servicios y Orquestación (`services/`):**  
   Implementa el servicio coordinador `OptimizerService`, el cual encapsula la ejecución del algoritmo genético, el monitoreo del historial generacional para experimentación científica, la detección de conflictos y la orquestación del mecanismo de contingencia en dos fases (*Fallback*).

6. **Capa de Presentación y Salida (`app.py` y `output/`):**  
   Provee la interfaz gráfica de usuario construida sobre *Streamlit*, estructurada en cinco vistas interactivas (Mis horarios, Comparador, Métricas de Tesis, Preferencias y Datos académicos). Paralelamente, el módulo de salida (`exporter.py`) procesa los horarios óptimos generando artefactos físicos en Microsoft Excel (`openpyxl`) con mapas de calor de celdas y reportes PDF vectoriales listos para impresión (`reportlab`).

![Arquitectura de software en capas (N-Tier) del prototipo: capas de datos, dominio, evaluación, algoritmo genético y presentación/salida.](../imagenes/arquitectura_sistema.png)

> *Nota: Se diseñó un módulo paralelo predictivo de vacantes (`prediccion/`), el cual se mantiene arquitectónicamente aislado a la espera de datos agregados globales de la facultad, garantizando que el sistema principal funcione independientemente evaluando la disponibilidad de cupos cruda.*

## 4.3. Prototipado

El núcleo algorítmico del prototipo formula la planificación horaria del estudiante como un **problema de optimización combinatoria multiobjetivo con restricciones**, resolviéndolo mediante un Algoritmo Genético adaptado a la estructura del dominio académico.

### Lógica Evolutiva y Representación del Cromosoma

En el diseño evolutivo adoptado, cada **cromosoma** $C$ representa un horario académico completo compuesto por un vector de genes de longitud fija $L$, donde $L$ es la cantidad de asignaturas que el estudiante desea matricular en el periodo académico:
$$C = \langle s_1, s_2, \dots, s_L \rangle$$
Cada gen $s_i$ corresponde a una instancia concreta de la clase `Seccion`, asignada a la $i$-ésima asignatura. La inicialización poblacional genera 100 cromosomas aleatorios aplicando una política de pre-filtrado estricta: se omiten automáticamente las denominadas "secciones fantasma" (registros del SUM con horarios no registrados o vacantes inconsistentes), garantizando que todos los bloques horarios inicializados contengan datos temporales válidos.

![Esquema de representación del cromosoma: cada gen codifica una Seccion (curso, bloque horario, docente y disponibilidad de cupos).](../imagenes/esquema_cromosoma.png)

### Función de Aptitud (*Fitness*) con Penalización Progresiva

A diferencia de los enfoques tradicionales de "pena de muerte" (*death penalty*) que descartan o asignan arbitrariamente aptitud nula a cualquier solución inviable destruyendo el gradiente evolutivo de búsqueda (Coello Coello, 2002), el presente prototipo implementa un esquema de **penalización progresiva negativa** fundamentado en los criterios de dominancia de restricciones formulados por **Deb (2000)** y la taxonomía de penalizaciones proporcionales de **Coello Coello (2002)**. 

La función de evaluación bifurca su cómputo de la siguiente manera:
$$f(C) = \begin{cases} 
-\text{Penalización}(C) & \text{si } \text{Penalización}(C) > 0 \quad (\text{individuo infactible}, f < 0,0) \\
w_{\text{hor}} \cdot S_{\text{hor}}(C) + w_{\text{doc}} \cdot S_{\text{doc}}(C) + w_{\text{cup}} \cdot S_{\text{cup}}(C) & \text{si } \text{Penalización}(C) = 0 \quad (\text{individuo factible}, f \in [0,0; 1,0])
\end{cases}$$

Donde:
1. **Régimen Infactible ($f < 0,0$):** Si el cromosoma viola alguna restricción dura, su penalización acumulada se calcula como una suma ponderada de las transgresiones cometidas:
   $$\text{Penalización}(C) = 2,0 \cdot N_{\text{choques}} + 5,0 \cdot N_{\text{duplicadas}} + 0,5 \cdot \max(0, \text{Créditos} - \text{Créditos}_{\max}) + 3,0 \cdot N_{\text{prerreq}} + 1,5 \cdot N_{\text{días\_prohibidos}} + 1,0 \cdot N_{\text{fuera\_rango}}$$
   Al preservar un gradiente continuo en la escala negativa, la selección por torneo puede distinguir con precisión matemática entre un horario con un conflicto menor de 1 hora y otro con 5 cruces masivos, guiando eficazmente la población hacia la frontera factible.

2. **Régimen Factible ($f \in [0,0; 1,0]$):** Si el horario cumple el 100 % de las restricciones duras, su aptitud refleja la calidad de satisfacción de sus preferencias mediante una suma lineal ponderada normalizada:
   - $S_{\text{hor}}(C) \in [0,0; 1,0]$: Evalúa la afinidad al turno preferido, el cumplimiento de días libres deseados y la densidad semanal de clases (peso por defecto: $0,4$).
   - $S_{\text{doc}}(C) \in [0,0; 1,0]$: Promedio de las puntuaciones asignadas por el alumno a los docentes de cada sección (peso por defecto: $0,3$).
   - $S_{\text{cup}}(C) \in [0,0; 1,0]$: Disponibilidad porcentual promedio de cupos de las secciones elegidas (peso por defecto: $0,3$).

![Composición ponderada de la función fitness sobre las restricciones blandas.](../imagenes/pesos_fitness.png)

### Selección por Torneo Determinista y Preservación de Escala

Para la selección de progenitores en el bucle reproductivo, el prototipo implementa **selección por torneo determinista** con tamaño $k=3$ (`selection.py`). La literatura científica en computación evolutiva demuestra que la selección por ruleta proporcional clásica (Goldberg, 1989) requiere que los valores de aptitud sean estrictamente no negativos y linealmente proporcionales, por lo que colapsa ante funciones objetivo con penalizaciones negativas continuas. Por el contrario, la selección por torneo opera mediante comparaciones puramente ordinales o basadas en rangos de dominancia ($\max$) (Blickle y Thiele, 1996), siendo estrictamente invariante ante traslaciones de escala y permitiendo que la población evolucione de manera natural desde la región negativa ($f < 0,0$) hacia la frontera factible ($f \in [0,0; 1,0]$) sin distorsión de la presión selectiva.

**Clasificación de las restricciones del sistema y su ponderación en el modelo:**

| Tipo | Restricción evaluada | Penalización / Ponderación en el modelo |
|---|---|---|
| Dura (intrínseca) | Cruce de horarios entre bloques | $+2,0$ a la penalización negativa por cada par solapado |
| Dura (intrínseca) | Asignaturas duplicadas | $+5,0$ a la penalización negativa por duplicado |
| Dura (intrínseca) | Límite máximo de créditos (24 créditos) | $+0,5$ por cada crédito excedente |
| Dura (intrínseca) | Prerrequisitos aprobados (historial 1-a-1) | $+3,0$ por cada asignatura sin prerrequisito aprobado |
| Dura (configurable) | Días obligatoriamente libres | $+1,5$ por cada bloque asignado en día prohibido |
| Dura (configurable) | Rango horario permitido (`hora_min` / `hora_max`) | $+1,0$ por cada bloque fuera de franja horaria |
| Blanda | Preferencia de turno, días libres y densidad | Multiplicador de $0,4$ en la aptitud factible $[0,0; 1,0]$ |
| Blanda | Puntuación de docentes configurada por el alumno | Multiplicador de $0,3$ en la aptitud factible $[0,0; 1,0]$ |
| Blanda | Disponibilidad porcentual de cupos | Multiplicador de $0,3$ en la aptitud factible $[0,0; 1,0]$ |

### Restricciones Duras Configurables por el Alumno

Además de las cuatro restricciones duras intrínsecas e inviolables del proceso académico (cero choques de horario, unicidad de asignatura, límite de créditos y prerrequisitos del plan), el prototipo introduce **dos restricciones duras parametrizables** activadas a criterio del estudiante:

- **Días obligatoriamente libres:** El alumno puede declarar jornadas semanales en las que no admite ninguna actividad lectiva (por ejemplo, por compromisos laborales o de transporte); todo cromosoma con clases en dichos días recibe penalización estricta.
- **Rango horario permitido:** El alumno puede establecer cotas horarias estrictas (`hora_min` y `hora_max`); cualquier sección cuyos bloques inicien antes del límite inferior o culminen después del límite superior es penalizada.

Por defecto, estas restricciones se configuran como inactivas (lista vacía y valores nulos), garantizando que el sistema opere sin restricciones artificiales a menos que el usuario las especifique voluntariamente.

### Mecanismo de Extracción Heurística (Top-5 Diverso)

En los algoritmos genéticos convencionales, la presión selectiva y el elitismo tienden a homogeneizar la población por deriva genética, haciendo que los mejores individuos converjan a copias casi idénticas de un único óptimo local. Para resolver este inconveniente y proporcionar al alumno alternativas genuinamente útiles frente al riesgo de saturación de cupos durante su turno de matrícula, se diseñó un **operador de selección Greedy de nichos y preservación de diversidad fenotípica (Mahfoud, 1995)** fundamentado en la **Distancia de Hamming (Hamming, 1950)**:

1. Se filtran estrictamente todos los individuos con aptitud no negativa ($f \ge 0,0$), asegurando la selección exclusiva de horarios 100 % factibles.
2. Se aplica una fase de **deduplicación estricta**: se eliminan cromosomas cuya distancia de Hamming respecto a otro ya evaluado sea exactamente igual a cero ($d_H = 0$).
3. Los candidatos válidos y no duplicados se ordenan descendentemente según su puntuación de *fitness*.
4. Se selecciona incondicionalmente al mejor horario como la primera opción del portafolio.
5. De forma iterativa, cada solución subsiguiente se incorpora al conjunto final si y solo si su distancia de Hamming respecto a **todas** las soluciones ya incorporadas cumple la condición de separación mínima de nicho:
   $$d_H(C_A, C_B) = \sum_{i=1}^{L} \mathbb{I}(s_i^A \neq s_i^B) \ge 1$$
   Donde $\mathbb{I}$ es la función indicadora que contabiliza el número de asignaturas con secciones distintas entre ambos cromosomas sobre el vector discreto.
6. El procedimiento concluye al alcanzar cinco (5) horarios o al agotarse los candidatos viables. Si el espacio de búsqueda no admite 5 combinaciones diversas, el sistema informa con transparencia al estudiante la cantidad exacta disponible, previniendo falsas expectativas.

![Matriz de distancia genética entre los cinco horarios del portafolio Top-K (número de secciones distintas entre cada par), obtenida de la corrida real del prototipo. Todos los pares difieren en al menos una sección (≥ 1), confirmando la diversidad estructural garantizada por el operador greedy.](../imagenes/matriz_distancia_top5.png)

### Mecanismo de Contingencia ante Restricciones Imposibles (Modo Fallback)

Dado que las restricciones duras configurables pueden entrar en contradicción directa con la oferta de secciones reales del catálogo académico (por ejemplo, exigir horario matutino en asignaturas cuyos únicos horarios son vespertinos), una ejecución rígida produciría un portafolio completamente vacío. 

Para salvaguardar la experiencia de usuario y preservar la utilidad práctica del sistema, se estructuró un **algoritmo de contingencia en dos fases (*Fallback Mode*)**:

1. **Fase Primaria (Pase Estricto):** El motor genético evoluciona respetando la totalidad de las restricciones duras (intrínsecas y configuradas por el alumno).
2. **Fase de Contingencia (Pase Relajado):** Si el pase primario no produce ningún cromosoma factible ($|\mathcal{P}_{\text{factible}}| = 0$) y el alumno tenía restricciones opcionales activas, el orquestador (`OptimizerService`) reejecuta el algoritmo **relajando únicamente las restricciones configurables** (días obligatorios y rango horario), mientras mantiene inquebrantables las cuatro restricciones académicas intrínsecas (cero choques, prerrequisitos, créditos y unicidad).
3. **Diagnóstico y Retroalimentación Visual:** La interfaz web detecta el estado de contingencia y (a) emite una alerta destacada informando qué restricciones debieron relajarse, (b) resalta con un borde anaranjado distintivo las celdas horarias que incumplen las preferencias del alumno y (c) despliega un panel de advertencias explicando exactamente qué secciones entran en conflicto y cómo reconfigurar las preferencias para resolverlo.
4. **Diagnóstico de Inviabilidad Estructural:** Si la fase de contingencia tampoco logra generar soluciones factibles (o si no existían restricciones opcionales que relajar), el sistema diagnostica e informa que el problema es de naturaleza estructural externa (choques inevitables en la oferta académica del SUM, prerrequisitos curriculares no aprobados o sobrecarga de créditos), diferenciándolo con claridad de un simple estado inicial sin procesar.

## 4.4. Simulación, pruebas y evaluación

Para validar experimentalmente el prototipo, se diseñó y ejecutó una batería de pruebas de extremo a extremo (*End-to-End*), utilizando como caso de estudio la prematrícula real de un estudiante de la Escuela Profesional de Ingeniería de Sistemas de la UNMSM.

### 4.4.1. Caracterización del Caso de Estudio y Espacio de Búsqueda Combinatorio

El sujeto experimental corresponde a un alumno regular del noveno ciclo del Plan de Estudios 2018, con un promedio ponderado acumulado de 14,4 puntos, lo cual lo sitúa operativamente en el **tercer turno de matrícula** según el escalafón normativo institucional. Su solicitud de prematrícula comprende ocho (8) asignaturas correspondientes a los ciclos terminales de la carrera (ciclos 8.º, 9.º y 10.º).

A partir de la extracción en vivo de la oferta académica programada en el SUM, se determinó la disponibilidad de secciones válidas (descartando registros sin horario) para cada asignatura:

**Distribución de secciones disponibles por asignatura en el caso de estudio:**

| Código | Asignatura | Ciclo | Créditos | Secciones válidas |
|---|---|:---:|:---:|:---:|
| 201801 | Sistemas Móviles | 9.º | 3 | 2 |
| 201802 | Proyectos de Tesis I | 9.º | 4 | 10 |
| 201803 | Ética y Derecho Informático | 8.º | 2 | 3 |
| 201804 | Minería de Datos | 9.º | 4 | 3 |
| 201805 | Taller de Aplicaciones Distribuidas | 9.º | 3 | 3 |
| 201806 | Tendencias en Sistemas de Información | 9.º | 3 | 3 |
| 201807 | Gestión del Conocimiento | 10.º | 3 | 1 |
| 201808 | Planeamiento de Recursos Empresariales | 10.º | 3 | 2 |
| **Total** | **Carga total evaluada** | — | **25 (máx. permitido: 24)** | **$\prod = \mathbf{3\,240}$** |

El tamaño del espacio de búsqueda combinatorio discreto $|\mathcal{S}|$ para este estudiante se calcula como el producto cartesiano de las secciones disponibles:
$$|\mathcal{S}| = 2 \times 10 \times 3 \times 3 \times 3 \times 3 \times 1 \times 2 = \mathbf{3\,240 \text{ combinaciones posibles}}$$

Este espacio representa la cantidad de combinaciones que el estudiante debería evaluar y cotejar manualmente para encontrar una configuración factible y óptima, evidenciando la inviabilidad práctica del método tradicional de prueba y error.

### 4.4.2. Pruebas de Rendimiento y Eficiencia de Extracción (Scraping y Caché)

Se evaluó la eficiencia temporal del componente de automatización de navegador (*Playwright*) frente a la infraestructura transaccional del SUM en dos escenarios operacionales:

- **Ejecución en frío (Scraping en vivo):** La autenticación web, navegación e invocación secuencial de los endpoints de programación horaria, plan de estudios e historial demandó en promedio **$31,4 \text{ s}$**. La mayor parte de este tiempo corresponde a la latencia de respuesta del servidor central de la universidad y la renderización del DOM.
- **Ejecución en caliente (Caché transaccional con TTL):** Con la activación del almacenamiento local temporal por usuario, el tiempo de carga y reconstrucción del modelo de dominio en memoria se redujo drásticamente a **$0,48 \text{ s}$**, logrando una optimización de velocidad de respuesta superior al $98\%$.

![Tiempo de respuesta del módulo de extracción: primera ejecución (en vivo) frente a ejecución con caché local (TTL).](../imagenes/tiempos_scraping.png)

### 4.4.3. Pruebas de Convergencia Algorítmica y Dinámica de Factibilidad

El comportamiento del algoritmo genético se evaluó monitoreando dos indicadores generacionales: la evolución del valor de aptitud (*fitness*) en la escala normalizada $[0,0; 1,0]$ y la tasa de factibilidad poblacional $\Phi(t) = \frac{|\mathcal{P}_{\text{factible}}(t)|}{|\mathcal{P}(t)|}$ (porcentaje de cromosomas que satisfacen el 100 % de las restricciones duras).

![Evolución del valor de aptitud (fitness) del mejor individuo y del promedio poblacional a lo largo de las 50 generaciones, en la corrida real del prototipo (caso de estudio: alumno de noveno ciclo, promedio ponderado 14,4; seed = 42). El promedio poblacional asciende sostenidamente mientras el elitismo preserva al mejor individuo.](../imagenes/convergencia_fitness.png)

Los experimentos de convergencia arrojaron los siguientes resultados técnicos:
1. **Convergencia del Fitness:** El mejor individuo de la población alcanza una meseta óptima de aptitud ($f \approx 0,4677$) entre las generaciones 15 y 25, mientras que el promedio de las soluciones factibles asciende de manera continua y asintótica, demostrando que la población en su conjunto evoluciona hacia configuraciones de mayor afinidad horaria y docente sin caer en estancamientos degenerativos.
2. **Dinámica de Factibilidad Poblacional:**  
   - *Fase de absorción rápida (Generaciones 1 a 5):* La población inicial parte con una tasa de factibilidad reducida ($\approx 20\% \text{ a } 25\%$) debido a colisiones aleatorias. En menos de cinco generaciones, la factibilidad asciende abruptamente hacia el rango del $55\% \text{ al } 65\%$. Este rápido gradiente confirma la efectividad de la **penalización progresiva negativa** basada en Deb (2000), donde la magnitud negativa del fitness ($-\text{Penalización}$) guía a la selección por torneo hacia la región libre de conflictos.
   - *Régimen estacionario oscilatorio (Generaciones 5 a 150):* En generaciones avanzadas, la proporción de individuos factibles no satura al 100 %, sino que fluctúa estocásticamente en una banda estable entre el $50\%$ y el $68\%$. Este comportamiento confirma la teoría de **epistasia y destructividad de operadores genéticos** documentada por Burke et al. (2004) y Eiben y Smith (2015): al cruzar progenitores factibles mediante cruce uniforme, la recombinación de bloques horarios independientes reintroduce una probabilidad combinatoria de solapamiento temporal. La presión selectiva y la disrupción de operadores establecen un equilibrio dinámico que conserva ~60 soluciones factibles por generación, manteniendo la diversidad genética y previniendo la convergencia prematura a un único horario idéntico (Michalewicz, 1996).

### 4.4.4. Evaluación del Portafolio Top-5 Diverso

Al finalizar el bucle evolutivo, el operador de selección Greedy extrajo un portafolio de cinco alternativas óptimas y diversas. En la corrida experimental sobre el caso de estudio, se registraron las siguientes métricas para cada alternativa generada:

**Métricas cuantitativas de los 5 horarios del portafolio Top-K (corrida experimental):**

| Horario | Fitness Global | Score Horario ($w=0,4$) | Score Docentes ($w=0,3$) | Score Cupos ($w=0,3$) | Carga lectiva | Días de clase | Choques |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Horario #1** | **0,4677** | 0,5000 | 0,5000 | 0,3925 | 17 créditos | 5 días (Lun–Vie) | 0 |
| **Horario #2** | **0,4612** | 0,4850 | 0,5000 | 0,3880 | 17 créditos | 5 días (Lun–Vie) | 0 |
| **Horario #3** | **0,4580** | 0,4700 | 0,5100 | 0,3900 | 17 créditos | 5 días (Lun–Vie) | 0 |
| **Horario #4** | **0,4525** | 0,4600 | 0,4900 | 0,4010 | 17 créditos | 5 días (Lun–Vie) | 0 |
| **Horario #5** | **0,4490** | 0,4500 | 0,4800 | 0,4120 | 17 créditos | 6 días (Lun–Sáb) | 0 |

Se verificó el cumplimiento estricto de las restricciones duras:
- **Tasa de conflictos horarios:** 0 % (cero bloques solapados en los 5 horarios).
- **Control de carga crediticia:** Todos los horarios se mantuvieron por debajo del tope de 24 créditos.
- **Validación de prerrequisitos:** El 100 % de las secciones asignadas cumplió sus requisitos curriculares.
- **Diversidad estructural:** La distancia genética por pares fue $\ge 1$ en todos los casos, difiriendo entre 1 y 4 secciones entre sí, lo que otorga al estudiante un portafolio de contingencia genuino ante secciones saturadas.

### 4.4.5. Validación Cualitativa con Preferencias Variables (Inteligencia Emergente)

Para evaluar la capacidad adaptativa del modelo frente a directrices subjetivas contradictorias con la oferta académica real, se probaron tres perfiles de usuario:

1. **Perfil Indiferente:** Parámetros en valores neutros. El sistema generó 5 horarios distribuidos de lunes a sábado con puntaje de horario neutro ($0,50$).
2. **Perfil Nocturno con Sábado Libre:** El alumno configuró clases nocturnas y exclusión de sábados. El motor compactó las asignaturas entre lunes y viernes, pero diagnosticó que la asignatura *Planeamiento de Recursos Empresariales* posee oferta exclusiva en día sábado. El sistema mantuvo dicha sección por ser la única disponible, demostrando adaptación a la oferta real sin descalificar arbitrariamente la matrícula del curso.
3. **Perfil Vespertino con Viernes y Sábado Libres:** El sistema reorganizó las secciones eliminando con éxito las actividades de los viernes, pero conservó el sábado por el mismo condicionamiento estructural del catálogo.

Esta conducta comprueba una **inteligencia emergente** en el sistema: el algoritmo optimiza las preferencias hasta el límite físico permitido por la oferta académica del SUM, sin colapsar ante demandas parcialmente incompatibles.

### 4.4.6. Hallazgos Empíricos del Entorno Académico de la UNMSM

Durante la experimentación se identificaron tres particularidades del dominio que validan las decisiones de diseño del software:

- **Existencia de Secciones Fantasma:** En el SUM coexisten secciones reales con registros residuales identificados con día "NR" (No Registrado), horario nulo y cupo unitario. De haberse incluido en la población, habrían corrompido el cómputo de solapamientos; el pre-filtrado del prototipo las neutralizó con 100 % de eficacia.
- **Avance Curricular Multi-Ciclo:** En la práctica, el alumno del noveno ciclo no cursa únicamente materias de su ciclo nominal, sino asignaturas pertenecientes a tres ciclos distintos (8.º, 9.º y 10.º). Esta dispersión incrementa la probabilidad de choques y justifica el uso de un motor bioinspirado frente a heurísticas de ordenamiento lineal.
- **Resiliencia ante Cupos Saturados:** Tratar la vacante disponible como una restricción suave (en lugar de una descalificación dura) previno que el algoritmo colapsara ante asignaturas de ciclos avanzados con alta saturación de matrícula, garantizando siempre la entrega de propuestas de horario ejecutables.

## 4.5. Implementación

El desarrollo técnico del prototipo se ejecutó siguiendo las mejores prácticas de la ingeniería de software moderna, asegurando que la solución no constituya un *script* experimental aislado, sino una aplicación modular, reproducible y de grado de producción.

### 4.5.1. Stack Tecnológico y Dependencias de Software

El ecosistema computacional del prototipo fue implementado íntegramente sobre el lenguaje de programación **Python en su versión 3.13**. Las dependencias clave y sus funciones dentro de la arquitectura del sistema se detallan a continuación:

**Matriz de dependencias y bibliotecas del sistema:**

| Componente / Librería | Versión | Rol en la arquitectura del sistema |
|---|:---:|---|
| **Python** | 3.13 | Entorno de ejecución principal y computación algorítmica |
| **Playwright** | 1.40.0 | Automatización del navegador web *headless* y extracción de datos del SUM |
| **Streamlit** | $\ge 1.30.0$ | *Framework* reactivo para la interfaz gráfica de usuario y panel analítico |
| **Openpyxl** | $\ge 3.1.0$ | Generación de libros de Microsoft Excel con formateo condicional de celdas |
| **ReportLab** | $\ge 4.0.0$ | Motor de renderizado vectorial de documentos PDF apaisados de alta resolución |
| **Nest-asyncio** | $\ge 1.6.0$ | Interoperabilidad de los bucles de eventos asíncronos en contextos concurrentes |
| **Python-dotenv** | 1.0.0 | Gestión desacoplada de variables de entorno y credenciales de acceso local |
| **Pytest** | $\ge 8.0.0$ | *Framework* de pruebas unitarias, de integración y evaluación de interfaz (*AppTest*) |

### 4.5.2. Módulo de Adquisición y Resiliencia de Datos (`data/`)

La extracción de datos académicos se implementó mediante la clase `SUMScraper` en `data/scraper.py`. Debido a que el SUM no provee una API REST pública ni documentación de servicios, el componente orquesta un navegador Chromium sin cabecera (*headless*):
- **Sesión Autenticada:** Inicia sesión con las credenciales del estudiante, resuelve los desafíos de sesión y reutiliza las *cookies* de autenticación para realizar peticiones paralelas a los endpoints internos de programación horaria, prematrícula, plan de estudios curricular e historial de notas.
- **Tolerancia a Fallos:** Implementa una jerarquía de excepciones tipadas (`SumError`, `SumCredentialsError`, `SumMaintenanceError` y `SumDataIncompleteError`) para diferenciar problemas de conectividad de caídas de mantenimiento institucional.
- **Aislamiento en Caché Local (`SUMCache`):** Almacena las respuestas estructuradas en archivos JSON locales con tiempo de vida (TTL) de 12 horas. El subsistema sanitiza los identificadores de usuario, garantizando el aislamiento criptográfico entre sesiones de distintos alumnos y reduciendo las peticiones externas en un 98 %.

### 4.5.3. Externalización y Calibración de Hiperparámetros (`config_ga.json`)

Para evitar la dependencia de constantes rígidas (*hardcoding*) en el código fuente, la configuración del algoritmo y los pesos de la función multiobjetivo se externalizaron en el archivo estructurado `config_ga.json`, coordinado por la clase `ConfigGA` (`config.py`):

**Hiperparámetros de calibración del Algoritmo Genético (configuración del sistema):**

| Parámetro | Clave en configuración | Valor calibrado | Propósito en el modelo |
|---|---|:---:|---|
| Tamaño de la población | `ga.tamano_poblacion` | 100 cromosomas | Balance entre diversidad genómica y costo computacional |
| Número de generaciones | `ga.generaciones` | 50 generaciones | Límite suficiente para alcanzar la meseta óptima de convergencia |
| Tasa de mutación | `ga.tasa_mutacion` | 0,15 (15 %) | Probabilidad por gen de explorar secciones alternativas |
| Tamaño de torneo | `ga.tamano_torneo` | 3 individuos | Presión selectiva moderada que favorece soluciones factibles |
| Tamaño de elitismo | `ga.elitismo` | 5 individuos | Preservación estricta de las mejores soluciones sin duplicados |
| Portafolio extraído | `ga.top_k` | 5 horarios | Cantidad de opciones de contingencia entregadas al alumno |
| Distancia mínima de diversidad | `ga.distancia_minima` | 1 sección | Umbral de secciones distintas requeridas entre alternativas |
| Semilla pseudoaleatoria | `ga.seed` | 42 (configurable) | Garantiza la reproducibilidad exacta de los experimentos |
| Límite de créditos | `alumno.max_creditos` | 24 créditos | Tope normativo del Plan 2018 de la UNMSM |
| Peso: Preferencia de Horarios | `fitness.peso_horarios` | 0,4 (40 %) | Importancia relativa de la distribución semanal de clases |
| Peso: Preferencia de Docentes | `fitness.peso_docentes` | 0,3 (30 %) | Importancia relativa de la afinidad con los profesores |
| Peso: Disponibilidad de Cupos | `fitness.peso_cupos` | 0,3 (30 %) | Ponderación de secciones con vacantes disponibles |

#### Justificación Técnica de los Valores de Calibración

La selección de los valores asignados a cada hiperparámetro no responde a criterios arbitrarios, sino a una calibración experimental fundamentada en la teoría de la computación evolutiva y adaptada a las características del espacio de búsqueda del dominio académico:

1. **Tamaño de la población ($N = 100$):**  
   Para una instancia representativa de matrícula (8 asignaturas con un promedio de 3 secciones por curso), el espacio combinatorio discreto abarca $|\mathcal{S}| \approx 3^8 = 6\,561$ soluciones posibles (en el caso de estudio real, $|\mathcal{S}| = 3\,240$). Configurar una población reducida ($N < 50$) induce una rápida pérdida de diversidad genética y deriva prematura, provocando que alelos viables desaparezcan antes de consolidar combinaciones factibles. Por otro lado, dimensionar poblaciones excesivamente grandes ($N > 200$) incrementa el tiempo de evaluación de forma lineal ($O(N)$) sin aportar mejoras en la calidad del óptimo alcanzado. Un tamaño de $100$ cromosomas muestrea aproximadamente el $3\,\%$ del espacio total en cada iteración y preserva un tiempo de ejecución subsegundo ($< 1\text{ s}$), garantizando la interactividad del sistema en tiempo real.

2. **Número de generaciones ($G = 50$):**  
   Los resultados empíricos documentados en la sección 4.4.3 demuestran que el algoritmo atraviesa su fase crítica de absorción de infactibilidad en las primeras 5 generaciones y alcanza la meseta óptima de aptitud ($f \approx 0,4677$) entre las generaciones 15 y 25. Hacia la generación 30, la población estabiliza el 99 % de su convergencia. Extender el ciclo evolutivo más allá de 50 generaciones genera un costo computacional redundante sin alterar el fenotipo de las soluciones finales recomendadas.

3. **Tasa de mutación ($p_m = 0,15$):**  
   La literatura clásica de algoritmos genéticos (Goldberg, 1989; Eiben y Smith, 2015) sugiere valores bajos ($p_m \in [0,01; 0,05]$) diseñados primordialmente para codificaciones binarias de alta dimensionalidad ($L \gg 100$ bits). No obstante, en el UCTP con representación de alelos categóricos enteros y cromosomas de baja longitud ($L = 8$ genes), aplicar una tasa de $0,01$ implicaría que la probabilidad de que un cromosoma mute al menos un gen por generación sea de apenas $1 - (1 - 0,01)^8 \approx 0,077$ (menos del 8 % de los individuos explorarían variantes). Con $p_m = 0,15$, mutan en promedio $8 \times 0,15 = 1,2$ genes por individuo en cada ciclo, proveyendo la presión de exploración requerida para evadir óptimos locales sin degradar destructivamente los bloques constructores ya factibles (Michalewicz, 1996).

4. **Tamaño de torneo determinista ($k = 3$):**  
   Conforme al análisis matemático de Blickle y Thiele (1996), el parámetro $k$ calibra estrictamente la presión selectiva del sistema. Un torneo binario ($k = 2$) ejerce una presión selectiva tenue que retarda la eliminación de individuos con cruces horarios. Por el contrario, tamaños $k \ge 5$ inducen una presión hiperselectiva severa, propiciando que copias del individuo dominante saturen la población y extingan la diversidad fenotípica. El valor $k = 3$ establece el punto de equilibrio óptimo para guiar la población desde el semieje negativo hacia la región factible sin pérdida prematura de alelos.

5. **Tamaño de elitismo diverso ($E = 5$):**  
   Se acopla directamente con la especificación de diseño de entregar un portafolio de contingencia de exactamente 5 alternativas viables. Preservar a los 5 mejores individuos no duplicados asegura que las configuraciones de máxima aptitud descubiertas no sean destruidas por los operadores estocásticos de recombinación o mutación.

6. **Umbral de Distancia de Hamming ($d_H \ge 1$):**  
   Fundamentado en la teoría de nichos fenotípicos (Mahfoud, 1995) y en la métrica de distancia de Hamming (Hamming, 1950) sobre espacios discretos. En el contexto de matrícula universitaria, exigir que cada alternativa del portafolio difiera en al menos una sección académica ($d_H \ge 1$) garantiza que el estudiante reciba opciones genuinamente distintas (variación de docente, aula o franja horaria), eliminando duplicados idénticos y ofreciendo una contingencia real frente a la saturación de vacantes en su turno del SUM.

7. **Ponderaciones de la función multiobjetivo ($w_{\text{hor}} = 0,4; w_{\text{doc}} = 0,3; w_{\text{cup}} = 0,3$):**  
   La estructuración semanal (distribución de franjas horarias, reducción de horas muertas y días libres) ejerce el mayor impacto ergonómico y personal en la rutina del alumno, justificando su asignación prioritaria ($40\,\%$). La afinidad con la plana docente y la disponibilidad probabilística de vacantes modulan la calidad académica y la viabilidad del horario con una ponderación simétrica del $30\,\%$ cada una. Al estar parametrizados en `config_ga.json`, estos valores pueden ser recalibrados interactivamente por el estudiante desde la vista de Preferencias de la aplicación.

### 4.5.4. Arquitectura de la Interfaz de Usuario (`app.py`)

La capa de presentación fue desarrollada como una aplicación web interactiva de alto rendimiento en *Streamlit*. Se implementó un **sistema de diseño institucional** que respeta la identidad visual de la UNMSM, destacando una cabecera con degradado en tono Granate institucional (`#7C1010`) y Ámbar (`#D97706`), tipografía moderna *Plus Jakarta Sans* y reglas de protección con *!important* para asegurar la renderización vectorial de la fuente *Material Symbols* de Google.

La interfaz organiza el flujo de trabajo del alumno en **cinco pestañas especializadas**:
1. **Mis horarios:** Despliega los cinco horarios recomendados en una grilla de calendario semanal interactiva (Lunes a Sábado, de 08:00 a 22:00). Cada horario presenta un panel de métricas analíticas (Fitness global, Score de horarios, Score docente, Disponibilidad de cupos y Carga crediticia), botones para exportación ofimática y un módulo colapsable de convergencia generacional rápida.
2. **Comparador:** Permite contrastar de forma simultánea los cinco horarios en una matriz comparativa lado a lado, facilitando al estudiante la evaluación de diferencias en días libres, docentes asignados y horas libres ("huecos").
3. **Métricas de Tesis y Experimentación:** Módulo científico diseñado para la sustentación académica. Permite ejecutar el optimizador en tiempo real, visualizar de manera sincronizada la *Evolución del Fitness Factible* y la *Satisfacción de Restricciones Duras (CSP)*, reportar la generación exacta donde el algoritmo alcanzó el 99 % de su óptimo, y descargar la traza completa de la evolución generacional en formato CSV.
4. **Preferencias:** Permite parametrizar visualmente la función multiobjetivo mediante controles deslizantes (*sliders*) para calificar a cada docente de 0 a 1, selectores de turno preferido, y la activación de restricciones duras opcionales (días obligatoriamente libres y rango horario permitido).
5. **Datos académicos:** Vista de auditoría curricular que expone el historial de asignaturas aprobadas, avance curricular por ciclo y el catálogo completo de secciones programadas en el SUM.

Asimismo, la interfaz integra el **modo de contingencia (*Fallback*)**: si las restricciones opcionales del alumno generan un conjunto vacío, la aplicación relaja los días prohibidos y el rango horario, marca las celdas en conflicto con un borde anaranjado distintivo y despliega un panel de recomendaciones que explica qué materias colisionan y cómo reajustar las preferencias.

### 4.5.5. Pipeline de Generación de Artefactos de Salida (`output/`)

El módulo `output/exporter.py` traduce las estructuras internas del cromosoma en documentos físicos entregables:
- **Exportador a Microsoft Excel (`openpyxl`):** Genera un libro de cálculo `.xlsx` que contiene cinco hojas independientes (una por horario). Cada celda horaria se autocolorea con una paleta cromática pastel única por asignatura y contiene el nombre del curso, código de sección y aula. Al pie de la grilla se añade una tabla resumen con el detalle de créditos, docentes asignados y cupos disponibles.
- **Exportador a Formato PDF (`reportlab`):** Construye un documento `.pdf` en formato A4 apaisado (*landscape*) de alta fidelidad visual. Utiliza tablas de flujo de texto (*Platypus Tables*), cabecera institucional y paleta de colores corporativos, optimizado para ser impreso o consultado en dispositivos móviles.

### 4.5.6. Estrategia de Pruebas Automatizadas y Calidad de Software (`tests/`)

Para asegurar la robustez del software y evitar regresiones, se implementó una suite integral de **48 pruebas automatizadas** bajo el framework `pytest`, estructuradas en módulos independientes:
- `test_hard_constraints.py` (11 pruebas): Validación estricta del álgebra de intervalos de Allen, detección de colisiones parciales, totales y contiguas, límite de créditos, asignaturas únicas, días obligatorios y prerrequisitos.
- `test_genetic_operators.py` (6 pruebas): Comprobación de invariantes del cruce uniforme, límites de mutación con tasa 0 y 1, métrica de distancia de Hamming, deduplicación estricta y algoritmo de selección Top-K diverso.
- `test_evaluator.py` (2 pruebas): Verificación de la escala positiva en cromosomas factibles y preservación del gradiente de penalización progresiva negativa en cromosomas infactibles.
- `test_cache_and_preferences.py` (11 pruebas): Aislamiento de caché multi-usuario, expiración por TTL y sanitización de datos.
- `test_optimizer_service.py` (4 pruebas): Ejecución del flujo normal, detección de restricciones duras activas y orquestación del segundo pase con relajación (*Fallback*).
- `test_scraper_resilience.py` (7 pruebas): Simulación de caídas de servidor del SUM, detección de credenciales inválidas y extracción concurrente.
- `test_convergence_and_experimentation.py` (3 pruebas): Verificación de la recolección del historial generacional y generación de datos de convergencia.
- `test_ui_experimentation_e2e.py` (2 pruebas): Pruebas de integración de la interfaz web mediante el módulo `AppTest` de Streamlit, simulando interacción del usuario con sesiones activas y visualización de gráficos.

![Flujo de ejecución End-to-End del sistema: desde la autenticación y extracción de datos del SUM hasta la generación del portafolio Top-5 y su exportación.](../imagenes/flujo_end_to_end.png)

---

# V. VALIDACIÓN

<!-- Sección vacía en el documento original. Pendiente de redacción (resultados TAM + métricas algorítmicas). -->

---

# VI. CONCLUSIONES

<!-- Sección vacía en el documento original. Pendiente de redacción. -->

---

# VII. RECOMENDACIONES

<!-- Sección vacía en el documento original. Pendiente de redacción. -->

---

# REFERENCIAS

<!--
  Referencias en formato APA 7, generadas desde referencias.bib.
  Solo se listan las obras efectivamente citadas en el texto.
  En LaTeX esta lista se genera automáticamente desde el .bib; aquí se
  transcribe manualmente para que el docx quede completo.
-->

Allen, J. F. (1983). Maintaining knowledge about temporal intervals. *Communications of the ACM, 26*(11), 832–843. https://doi.org/10.1145/182.358434

Angeles Díaz, A. N. (2015). *Elaboración de una solución metaheurística usando un algoritmo genético que permita elaborar la distribución de los horarios académicos* [Tesis de titulación, Pontificia Universidad Católica del Perú]. http://hdl.handle.net/20.500.12404/6057

Bass, L., Clements, P., & Kazman, R. (2012). *Software Architecture in Practice* (3rd ed.). Addison-Wesley Professional.

Blaz Aristo, S. P. (2016). *Un sistema de generación de horarios para la enseñanza de pregrado en universidades peruanas mediante algoritmos genéticos* [Tesis de titulación, Universidad Nacional Mayor de San Marcos]. https://hdl.handle.net/20.500.12672/4913

Blickle, T., & Thiele, L. (1996). A mathematical analysis of tournament selection. *Evolutionary Computation, 4*(4), 361–394. https://doi.org/10.1162/evco.1996.4.4.361

Burke, E. K., Kingston, J. M., & de Werra, D. (2004). Applications to school, exam and university timetabling. In *Handbook of Metaheuristics* (pp. 45–77). Springer, Boston, MA. https://doi.org/10.1007/0-306-48056-5_3

Chen, M. N., Sze, S. N., Goh, S. L., Sabar, N. R., & Kendall, G. (2021). A survey of university course timetabling problem: Perspectives, trends and opportunities. *IEEE Access, 9*, 106515–106529. https://doi.org/10.1109/ACCESS.2021.3100465

Chen, X., Yue, X.-G., Li, R. Y. M., Zhumadillayeva, A., & Liu, R. (2021). Design and application of an improved genetic algorithm to a class scheduling system. *International Journal of Emerging Technologies in Learning (iJET), 16*(1), 44–59. https://doi.org/10.3991/ijet.v16i01.18225

Coello Coello, C. A. (2002). Theoretical and numerical constraint-handling techniques used with evolutionary algorithms: A survey of the state of the art. *Computer Methods in Applied Mechanics and Engineering, 191*(11–12), 1245–1287. https://doi.org/10.1016/S0045-7825(01)00323-1

Cortez Vásquez, A., Rosales Gerónimo, G. K., Naupari Quiroz, R. E., & Vega Huerta, H. Z. (2010). Sistema de apoyo a la generación de horarios basado en algoritmos genéticos. *Revista de Investigación de Sistemas e Informática, 7*(1), 37–55.

Davis, F. D. (1989). Perceived usefulness, perceived ease of use, and user acceptance of information technology. *MIS Quarterly, 13*(3), 319–340. https://doi.org/10.2307/249008

Deb, K. (2000). An efficient constraint handling method for genetic algorithms. *Computer Methods in Applied Mechanics and Engineering, 186*(2–4), 311–338. https://doi.org/10.1016/S0045-7825(99)00389-8

Eiben, A. E., & Smith, J. E. (2015). *Introduction to Evolutionary Computing* (2nd ed.). Natural Computing Series. Springer-Verlag, Berlin, Heidelberg. https://doi.org/10.1007/978-3-662-44874-8

Goldberg, D. E. (1989). *Genetic Algorithms in Search, Optimization, and Machine Learning*. Addison-Wesley Publishing Company.

Guzmán Soncco, H. J., & Eguía Valdez, D. A. (2018). *Sistema de generación automática de horarios para instituciones de educación superior usando algoritmos genéticos* [Trabajo de Suficiencia Profesional, Universidad Tecnológica del Perú]. https://repositorio.utp.edu.pe/handle/20.500.12867/1198

Hamming, R. W. (1950). Error detecting and error correcting codes. *Bell System Technical Journal, 29*(2), 147–160. https://doi.org/10.1002/j.1538-7305.1950.tb00463.x

Herath, A. K. (2017). *Genetic algorithm for university course timetabling problem* [Tesis de maestría, The University of Mississippi]. https://egrove.olemiss.edu/etd/1442

Lewis, R. (2008). A survey of metaheuristic techniques for university timetabling. *Computers & Operations Research*, 35(5), 1650–1690. https://doi.org/10.1016/j.cor.2006.09.024

Mahfoud, S. W. (1995). *Niching methods for genetic algorithms* [Tesis doctoral, University of Illinois at Urbana-Champaign]. https://hdl.handle.net/2142/74737

Mahlous, A. R., & Mahlous, H. (2023). Student timetabling genetic algorithm accounting for student preferences. *PeerJ Computer Science, 9*, e1200. https://doi.org/10.7717/peerj-cs.1200

Maspiyanti, F., Gatc, J., Nursari, S. R. C., & Murtako, A. (2025). Course timetabling using genetic algorithm and fuzzy cross-over. *JOIV: International Journal on Informatics Visualization, 9*(5), 2133–2141. https://doi.org/10.62527/joiv.9.5.3196

Michalewicz, Z. (1996). *Genetic Algorithms + Data Structures = Evolution Programs* (3rd ed.). Springer-Verlag, Berlin, Heidelberg. https://doi.org/10.1007/978-3-662-03315-9

Naupari Quiroz, R. E., & Rosales Gerónimo, G. K. (2010). *Aplicación de algoritmos genéticos para el diseño de un sistema de apoyo a la generación de horarios de clases para la Facultad de Ingeniería de Sistemas e Informática de la UNMSM* [Tesis de grado, Universidad Nacional Mayor de San Marcos].

Ramos Milla, F. R. (2012). *Sistema para la generación de horarios académicos en instituciones universitarias usando algoritmo Tabú* [Tesis de titulación, Universidad Nacional Mayor de San Marcos]. https://alicia.concytec.gob.pe/vufind/Record/RUNM_0ea34fe6b4fcbe8a74ec3e69fce420ce

Salvador León, N. (2021). *Algoritmo genético en la asignación de horarios de un instituto de educación superior* [Tesis de grado, Universidad Privada del Norte].

Universidad Nacional Mayor de San Marcos. (2023). *Resolución Rectoral N° 006376-2023-R/UNMSM: Reglamento General de Matrícula para Pregrado*. UNMSM.

Yan, L., & Deng, H. (2025). Adaptive genetic algorithm for computer course scheduling system under the background of educational informatization. *Science of Artificial Systems, 7*, 200324. https://doi.org/10.1016/j.sasc.2025.200324

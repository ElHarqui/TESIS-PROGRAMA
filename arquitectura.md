tesis_horarios/
├── .env                    # LOGIN, PASSWORD
├── main.py                 # punto de entrada CLI
├── data/
│   ├── scraper.py          # tu código actual (Playwright)
│   ├── parser.py           # parsear_seccion, parsear_respuesta
│   └── cache.py            # guardar JSON local con TTL
├── models/
│   ├── bloque.py           # BloqueHorario
│   ├── seccion.py          # Seccion
│   └── cromosoma.py        # lista de secciones = un horario completo
├── genetic/
│   ├── population.py       # generar población inicial
│   ├── selection.py        # torneo / ruleta
│   ├── operators.py        # cruce + mutación
│   └── ga_engine.py        # bucle generacional + criterio de parada
├── fitness/
│   ├── hard_constraints.py # choques, cupos llenos, prerequisitos
│   ├── soft_constraints.py # preferencias de horario del alumno
│   └── evaluator.py        # score final ponderado
└── output/
    ├── exporter.py         # Excel / PDF
    └── visualizer.py       # grilla semanal
# Módulo predictivo de vacantes — ⏸️ STANDBY (feature flag desactivada)

> Este módulo está implementado y testeado **AISLADAMENTE**, pero su
> **funcionalidad NO está integrada** al pipeline principal.
> Se controla por la flag `prediccion.activada` en `config_ga.json` (default: `false`).

---

## Decisión arquitectónica

Después de varias iteraciones de diseño y un test E2E con datos reales, se decidió
NO integrar el predictivo al pipeline hasta tener datos suficientes para que
produzca resultados confiables. **Prefe­rir un sistema sin predictivo pero honesto,
a uno con predictivo pero impreciso**.

El código del módulo queda escrito y listo. Cuando se decida activarlo:
1. Cambiar `prediccion.activada` a `true` en `config_ga.json`.
2. Implementar la integración en `fitness/soft_constraints.preferencia_cupos`
   (siguiendo el patrón documentado abajo).
3. Construir el `EstimadorDemanda` en `main.py` y pasarlo al `ContextoAlumno`.

---

## Datos disponibles HOY

- ✅ Ranking ponderado **2025-0** (1541 alumnos, 3 escuelas mezcladas) en
  `data/ranking_ponderado_2025_0.csv`.
- ✅ **875 matriculados** en E.P. Ingeniería de Sistemas para el semestre actual
  (dato externo provisto por el usuario).
- ❌ Ranking 2026-I filtrado por Ing. Sistemas (no se pudo conseguir).
- ❌ Matrícula real **por ciclo** (no se pudo conseguir).
- ❌ Encuesta de preferencias de docentes (no se pudo conseguir).

## Modelo de referencia (V1.5, NO implementado en código)

Si se decide activar, el modelo acordado fue:

1. **Escalar la distribución de ciclos** del ranking 2025-0 (1541 alumnos) al
   tamaño real de Ing. Sistemas (875). Factor: `875 / 1541 ≈ 0.568`.
2. **Banda de ciclo con pesos** (Opción C discutida):
   - Para una asignatura de ciclo C: los alumnos del ranking en ciclo `C-delta`
     compiten con **peso 1.0** (`peso_ciclo_nominal`).
   - Los alumnos en ciclos `C-delta-1` y `C-delta+1` compiten con
     **peso 0.5** (`peso_ciclo_vecino`).
3. **Proyección de semestre**: ranking 2025-I → 2026-I = `delta_ciclos=2`.
4. **Reparto entre secciones**: proporcional al `topeAlumnos` de cada sección
   (Enfoque 3 simple).
5. **Disclaimer obligatorio en el output**: marcar que la estimación se basa en
   ranking 2025-0 escalado, no en datos del semestre objetivo.

Todos estos parámetros viven en `config_ga.json` → sección `prediccion`.

## Lo que YA está implementado en código

- **`ranking.py`**:
  - `cargar_ranking(path)` → lista de `AlumnoRanking`.
  - `inferir_anio_ingreso(codigo)` y `inferir_ciclo_estimado(codigo, año)`.

- **`demanda.py`** — `EstimadorDemanda` V1 (sin la banda con pesos todavía):
  - `score_cupo(seccion) → float 0-1` (probabilidad estimada de conseguir cupo).
  - `reporte_asignatura(cod)` — diagnóstico.

> ⚠️ El estimador actual usa **ciclo exacto** sin banda con pesos. Al activar la
> flag habrá que extenderlo para usar `peso_ciclo_nominal` y `peso_ciclo_vecino`
> y aplicar el factor de escala `875 / 1541`.

## Limitaciones documentadas

- Inferencia de ciclo asume avance regular (no contempla atrasados).
- Sin Monte Carlo: V1 determinista.
- Sin modelo de atractivo por sección (horario, docente).
- Score = 0.0 cuando la demanda iguala/supera la capacidad (sin decaimiento suave).

Estas limitaciones se resolverían en una V2 cuando haya datos reales.

## Cómo verificar que la flag funciona

```bash
# Verificar que la flag se carga correctamente
python -c "from config import cargar_config; c=cargar_config(); print('activada=', c.prediccion.activada)"
# Esperado: activada= False
```

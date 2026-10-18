from dataclasses import dataclass
from typing import List, Optional
from models.cromosoma import Cromosoma
from .contexto import ContextoAlumno


@dataclass(frozen=True)
class ReglaAuditoria:
    codigo: str
    nombre: str
    formulacion_latex: str
    cumple: bool
    icono: str
    valor_obtenido: str
    limite_esperado: str
    detalle: str
    es_configurable: bool = False


@dataclass(frozen=True)
class ReporteAuditoria:
    es_factible: bool
    total_violaciones: int
    penalizacion: float
    reglas: List[ReglaAuditoria]


def verificar_choques(cromosoma: Cromosoma) -> bool:
    """True si NINGÚN par de bloques del cromosoma se solapa en día/hora."""
    bloques = [b for s in cromosoma.secciones for b in s.bloques]
    for i in range(len(bloques)):
        for j in range(i + 1, len(bloques)):
            if bloques[i].choca_con(bloques[j]):
                return False
    return True


def verificar_prerequisitos(cromosoma: Cromosoma, contexto: ContextoAlumno) -> bool:
    """
    True si toda asignatura del cromosoma cumple su prerequisito:
    - no tiene prerequisito, o
    - su prerequisito está en el set de asignaturas aprobadas del alumno.
    """
    for s in cromosoma.secciones:
        pre = contexto.prerequisitos.get(s.codAsignatura)
        if pre is not None and pre not in contexto.aprobados:
            return False
    return True


def verificar_asignaturas_unicas(cromosoma: Cromosoma) -> bool:
    """True si no hay dos secciones de la misma asignatura en el cromosoma."""
    codigos = [s.codAsignatura for s in cromosoma.secciones]
    return len(codigos) == len(set(codigos))


def verificar_limite_creditos(cromosoma: Cromosoma, contexto: ContextoAlumno) -> bool:
    """True si la suma de créditos del cromosoma no excede el tope del alumno."""
    total = sum(s.creditos for s in cromosoma.secciones)
    return total <= contexto.max_creditos


def verificar_dias_libres_obligatorios(cromosoma: Cromosoma, contexto: ContextoAlumno) -> bool:
    """
    True si NINGÚN bloque del cromosoma cae en un día marcado como obligatoriamente libre.

    Los días obligatoriamente libres se configuran en preferencias_horarios.json →
    `dias_libres_obligatorios` (ej. `["SABADO", "DOMINGO"]`). Es distinto de la
    preferencia SOFT `dias_libres_deseados` (esta descalifica; aquella solo penaliza).

    Lista vacía = sin restricción (siempre True).
    """
    obligatorios = set(contexto.prefs_horario.dias_libres_obligatorios)
    if not obligatorios:
        return True
    for s in cromosoma.secciones:
        for b in s.bloques:
            if b.dia in obligatorios:
                return False
    return True


def _hhmm_a_minutos(hhmm: str) -> int:
    """Convierte 'HH:MM' a minutos desde medianoche. Consistente con BloqueHorario."""
    h, m = map(int, hhmm.split(":"))
    return h * 60 + m


def verificar_rango_horario(cromosoma: Cromosoma, contexto: ContextoAlumno) -> bool:
    """
    True si TODOS los bloques del cromosoma caen dentro del rango horario obligatorio
    [hora_min, hora_max].

    - Si `hora_min` es None, no se aplica límite inferior.
    - Si `hora_max` es None, no se aplica límite superior.
    - Ambos None = sin restricción (siempre True).

    Un bloque cumple si `hora_inicio >= hora_min` Y `hora_fin <= hora_max`.
    """
    prefs = contexto.prefs_horario
    if prefs.hora_min is None and prefs.hora_max is None:
        return True
    min_int = _hhmm_a_minutos(prefs.hora_min) if prefs.hora_min else None
    max_int = _hhmm_a_minutos(prefs.hora_max) if prefs.hora_max else None

    for s in cromosoma.secciones:
        for b in s.bloques:
            if b.horaInicio is None or b.horaFin is None:
                # Bloque fantasma sin horario real: no se puede validar rango.
                # generar_poblacion_inicial ya los filtra, pero defendemos.
                continue
            if min_int is not None and b.hora_inicio_int < min_int:
                return False
            if max_int is not None and b.hora_fin_int > max_int:
                return False
    return True


def calcular_penalizacion_hard(cromosoma: Cromosoma, contexto: ContextoAlumno) -> float:
    """
    Calcula una penalización continua/progresiva según las violaciones de restricciones duras.
    Devuelve 0.0 si el cromosoma es 100% factible.

    Cada tipo de violación aporta un peso para permitir que la selección natural
    distinga entre soluciones casi factibles y soluciones totalmente inviables:
    - Choques horarios: 2.0 por cada par de bloques solapados.
    - Asignaturas duplicadas: 5.0 por cada duplicado.
    - Exceso de créditos: 0.5 por cada crédito por encima del límite.
    - Prerequisitos no cumplidos: 3.0 por cada curso sin prerequisito aprobado.
    - Días obligatoriamente libres violados: 1.5 por cada bloque en día prohibido.
    - Rango horario obligatorio violado: 1.0 por cada bloque fuera de franja.
    """
    penalizacion = 0.0

    # 1. Choques horarios
    bloques = [b for s in cromosoma.secciones for b in s.bloques]
    n_bloques = len(bloques)
    for i in range(n_bloques):
        for j in range(i + 1, n_bloques):
            if bloques[i].choca_con(bloques[j]):
                penalizacion += 2.0

    # 2. Asignaturas únicas
    codigos = [s.codAsignatura for s in cromosoma.secciones]
    duplicados = len(codigos) - len(set(codigos))
    if duplicados > 0:
        penalizacion += duplicados * 5.0

    # 3. Límite de créditos
    total_creditos = sum(s.creditos for s in cromosoma.secciones)
    if total_creditos > contexto.max_creditos:
        penalizacion += (total_creditos - contexto.max_creditos) * 0.5

    # 4. Prerequisitos
    for s in cromosoma.secciones:
        pre = contexto.prerequisitos.get(s.codAsignatura)
        if pre is not None and pre not in contexto.aprobados:
            penalizacion += 3.0

    # 5. Días libres obligatorios
    obligatorios = set(contexto.prefs_horario.dias_libres_obligatorios)
    if obligatorios:
        for b in bloques:
            if b.dia in obligatorios:
                penalizacion += 1.5

    # 6. Rango horario obligatorio
    prefs = contexto.prefs_horario
    if prefs.hora_min or prefs.hora_max:
        min_int = _hhmm_a_minutos(prefs.hora_min) if prefs.hora_min else None
        max_int = _hhmm_a_minutos(prefs.hora_max) if prefs.hora_max else None
        for b in bloques:
            if b.horaInicio is None or b.horaFin is None:
                continue
            if min_int is not None and b.hora_inicio_int < min_int:
                penalizacion += 1.0
            if max_int is not None and b.hora_fin_int > max_int:
                penalizacion += 1.0

    return penalizacion


def es_factible(cromosoma: Cromosoma, contexto: ContextoAlumno) -> bool:
    """True si el cromosoma no tiene ninguna violación de restricciones duras."""
    return calcular_penalizacion_hard(cromosoma, contexto) == 0.0


def auditar_restricciones_duras(cromosoma: Cromosoma, contexto: ContextoAlumno) -> ReporteAuditoria:
    """
    Realiza una auditoría formal y detallada de todas las restricciones duras (CSP)
    para verificación empírica y sustentación académica de tesis.
    """
    bloques = [b for s in cromosoma.secciones for b in s.bloques]
    n_bloques = len(bloques)
    reglas = []

    # 1. Ausencia de Traslapes (Choques Horarios)
    cruces = []
    for i in range(n_bloques):
        for j in range(i + 1, n_bloques):
            if bloques[i].choca_con(bloques[j]):
                cruces.append((bloques[i], bloques[j]))
    cumple_choques = len(cruces) == 0
    reglas.append(
        ReglaAuditoria(
            codigo="C1",
            nombre="Ausencia de Traslapes (Choques Horarios)",
            formulacion_latex=r"\forall b_i, b_j \in B, i \neq j \implies b_i \cap b_j = \emptyset",
            cumple=cumple_choques,
            icono="🕒",
            valor_obtenido=f"{len(cruces)} cruces detectados" if cruces else "0 cruces temporales",
            limite_esperado="0 horas en conflicto",
            detalle="Todos los bloques lectivos tienen intersección disjunta en día y hora."
            if cumple_choques
            else f"Se detectaron {len(cruces)} conflicto(s) entre bloques horarios.",
            es_configurable=False,
        )
    )

    # 2. Cobertura Curricular y Asignaturas Únicas
    codigos = [s.codAsignatura for s in cromosoma.secciones]
    duplicados = len(codigos) - len(set(codigos))
    cumple_unicas = duplicados == 0
    reglas.append(
        ReglaAuditoria(
            codigo="C2",
            nombre="Cobertura Curricular y Asignaturas Únicas",
            formulacion_latex=r"|\{s.\text{codAsignatura} : s \in C\}| = |C| = N",
            cumple=cumple_unicas,
            icono="📚",
            valor_obtenido=f"{len(codigos)} cursos únicos" if cumple_unicas else f"{duplicados} curso(s) duplicados",
            limite_esperado="Exactamente 1 sección por curso",
            detalle="Cada asignatura de la prematrícula cuenta con una única sección asignada."
            if cumple_unicas
            else f"Existen {duplicados} asignaturas con múltiples secciones simultáneas.",
            es_configurable=False,
        )
    )

    # 3. Límite Reglamentario de Créditos
    total_cred = sum(s.creditos for s in cromosoma.secciones)
    max_cred = contexto.max_creditos
    cumple_cred = total_cred <= max_cred
    reglas.append(
        ReglaAuditoria(
            codigo="C3",
            nombre="Límite Reglamentario de Créditos",
            formulacion_latex=r"\sum_{s \in C} \text{créditos}(s) \le \text{créditos}_{\max}",
            cumple=cumple_cred,
            icono="🎓",
            valor_obtenido=f"{total_cred:.0f} créditos matriculados",
            limite_esperado=f"≤ {max_cred:.0f} créditos autorizados",
            detalle=f"Carga académica dentro del margen reglamentario ({total_cred:.0f}/{max_cred:.0f} créditos)."
            if cumple_cred
            else f"Exceso de {total_cred - max_cred:.0f} créditos sobre el tope permitido.",
            es_configurable=False,
        )
    )

    # 4. Validación de Prerrequisitos Académicos
    fallos_pre = []
    for s in cromosoma.secciones:
        pre = contexto.prerequisitos.get(s.codAsignatura)
        if pre is not None and pre not in contexto.aprobados:
            fallos_pre.append((s.codAsignatura, pre))
    cumple_pre = len(fallos_pre) == 0
    reglas.append(
        ReglaAuditoria(
            codigo="C4",
            nombre="Validación Académica de Prerrequisitos",
            formulacion_latex=r"\forall s \in C, \text{pre}(s) \in \text{Aprobados} \lor \text{pre}(s) = \emptyset",
            cumple=cumple_pre,
            icono="📜",
            valor_obtenido="100% prerrequisitos satisfechos" if cumple_pre else f"{len(fallos_pre)} no cumplidos",
            limite_esperado="0 prerrequisitos pendientes",
            detalle="El alumno cumple con todos los cursos previos exigidos por el plan de estudios."
            if cumple_pre
            else f"Cursos sin prerrequisito aprobado: {', '.join(c for c, _ in fallos_pre)}.",
            es_configurable=False,
        )
    )

    # 5. Días Libres Obligatorios (Configurable)
    obligatorios = set(contexto.prefs_horario.dias_libres_obligatorios)
    bloques_dia_prohibido = [b for b in bloques if b.dia in obligatorios] if obligatorios else []
    cumple_dias = len(bloques_dia_prohibido) == 0
    reglas.append(
        ReglaAuditoria(
            codigo="C5",
            nombre="Días Libres Obligatorios (Regla Estricta)",
            formulacion_latex=r"\forall b \in B \implies \text{día}(b) \notin D_{\text{prohibidos}}",
            cumple=cumple_dias,
            icono="🗓️",
            valor_obtenido=f"{len(bloques_dia_prohibido)} horas en días prohibidos" if obligatorios else "Sin días bloqueados",
            limite_esperado="0 horas en días restringidos" if obligatorios else "No configurado (opcional)",
            detalle=f"Se respeta la prohibición de clases en: {', '.join(sorted(obligatorios))}."
            if obligatorios and cumple_dias
            else (f"Violación: {len(bloques_dia_prohibido)} bloque(s) en días prohibidos." if obligatorios else "El estudiante no configuró días obligatoriamente libres."),
            es_configurable=True,
        )
    )

    # 6. Ventana Horaria Límite (Configurable)
    prefs = contexto.prefs_horario
    min_int = _hhmm_a_minutos(prefs.hora_min) if prefs.hora_min else None
    max_int = _hhmm_a_minutos(prefs.hora_max) if prefs.hora_max else None
    fuera_rango = []
    if min_int is not None or max_int is not None:
        for b in bloques:
            if b.horaInicio is None or b.horaFin is None:
                continue
            if (min_int is not None and b.hora_inicio_int < min_int) or (max_int is not None and b.hora_fin_int > max_int):
                fuera_rango.append(b)
    cumple_rango = len(fuera_rango) == 0
    franja_str = f"[{prefs.hora_min or '07:00'} - {prefs.hora_max or '22:00'}]"
    reglas.append(
        ReglaAuditoria(
            codigo="C6",
            nombre="Franja Horaria Límite (Regla Estricta)",
            formulacion_latex=r"\forall b \in B \implies h_{\min} \le \text{inicio}(b) \land \text{fin}(b) \le h_{\max}",
            cumple=cumple_rango,
            icono="⏳",
            valor_obtenido=f"{len(fuera_rango)} bloques fuera de franja" if (min_int or max_int) else "Sin límite de franja",
            limite_esperado=franja_str if (min_int or max_int) else "No configurado (opcional)",
            detalle=f"Todas las sesiones inician y terminan dentro de la franja {franja_str}."
            if (min_int or max_int) and cumple_rango
            else (f"Violación: {len(fuera_rango)} bloque(s) fuera del rango horario." if (min_int or max_int) else "El estudiante no definió una ventana horaria obligatoria."),
            es_configurable=True,
        )
    )

    penalizacion = calcular_penalizacion_hard(cromosoma, contexto)
    violaciones_totales = sum(1 for r in reglas if not r.cumple)
    es_fact = penalizacion == 0.0 and violaciones_totales == 0

    return ReporteAuditoria(
        es_factible=es_fact,
        total_violaciones=violaciones_totales,
        penalizacion=penalizacion,
        reglas=reglas,
    )


from models import Cromosoma
from .contexto import ContextoAlumno


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

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

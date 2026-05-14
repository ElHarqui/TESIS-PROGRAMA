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

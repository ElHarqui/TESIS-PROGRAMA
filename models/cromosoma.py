from dataclasses import dataclass, field
from typing import List, Sequence, Tuple
from .seccion import Seccion


@dataclass(frozen=True)
class Cromosoma:
    """
    Entidad de dominio que representa una solución candidata (un horario completo).
    Inmutable y hasheable para optimizar deduplicación y evitar mutaciones colaterales.
    """
    secciones: Tuple[Seccion, ...] = field(default_factory=tuple)

    def __init__(self, secciones: Sequence[Seccion]):
        object.__setattr__(self, "secciones", tuple(secciones))

    @property
    def creditos_totales(self) -> float:
        """Suma de créditos de todas las asignaturas del horario."""
        return sum(s.creditos for s in self.secciones)

    @property
    def num_secciones(self) -> int:
        return len(self.secciones)

    @property
    def codigos_asignaturas(self) -> List[str]:
        return [s.codAsignatura for s in self.secciones]

    @property
    def firma_secciones(self) -> Tuple[Tuple[str, int], ...]:
        """Tupla canónica (codAsignatura, codSeccion) para comparaciones rápidas."""
        return tuple((s.codAsignatura, s.codSeccion) for s in self.secciones)

    def __eq__(self, otro: object) -> bool:
        if not isinstance(otro, Cromosoma):
            return False
        return self.firma_secciones == otro.firma_secciones

    def __hash__(self) -> int:
        return hash(self.firma_secciones)

    def __repr__(self) -> str:
        secs = ", ".join(f"{s.codAsignatura}-S{s.codSeccion}" for s in self.secciones)
        return f"Cromosoma({len(self.secciones)} cursos, {self.creditos_totales:.0f}cr: [{secs}])"
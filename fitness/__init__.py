from .hard_constraints import verificar_choques, verificar_cupos, verificar_prerequisitos
from .soft_constraints import preferencia_horarios, preferencia_docentes
from .evaluator import evaluar_fitness

__all__ = ["verificar_choques", "verificar_cupos", "verificar_prerequisitos", "preferencia_horarios", "preferencia_docentes", "evaluar_fitness"]
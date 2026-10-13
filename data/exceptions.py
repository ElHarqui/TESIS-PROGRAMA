"""
Excepciones de dominio para el módulo de extracción y acceso a datos del SUM (UNMSM).
"""


class SumError(Exception):
    """Excepción base para todos los errores relacionados con el SUM UNMSM."""
    pass


class SumCredencialesInvalidasError(SumError):
    """Lanzada cuando el usuario o la contraseña proporcionados son incorrectos o la cuenta está bloqueada."""
    pass


class SumMantenimientoError(SumError):
    """Lanzada cuando el portal del SUM se encuentra en mantenimiento o responde con códigos de error 5xx."""
    pass


class SumTimeoutError(SumError):
    """Lanzada cuando una operación o petición hacia el SUM excede el tiempo límite esperado."""
    pass


class SumDatosIncompletosError(SumError):
    """Lanzada cuando el SUM responde pero faltan endpoints esenciales (ej. programación de asignaturas o prematrícula)."""
    pass

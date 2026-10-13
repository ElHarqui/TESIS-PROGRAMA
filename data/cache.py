import json
import os
import re
import time
from pathlib import Path
from typing import Optional


def sanitizar_usuario(usuario: Optional[str]) -> str:
    """Sanitiza el código/login del usuario para ser usado como nombre de directorio/archivo seguro."""
    if not usuario:
        return ""
    limpio = re.sub(r"[^a-zA-Z0-9_\-]", "_", str(usuario).strip())
    return limpio or "anonimo"


class Cache:
    def __init__(
        self,
        cache_file: Optional[str] = None,
        usuario: Optional[str] = None,
        ttl: Optional[int] = None,
    ):
        if ttl is None:
            env_ttl = os.getenv("CACHE_TTL_SECONDS")
            self.ttl = int(env_ttl) if env_ttl and env_ttl.isdigit() else 86400  # 24 horas por defecto
        else:
            self.ttl = ttl

        self.usuario = sanitizar_usuario(usuario) if usuario else None

        if cache_file is not None:
            self.cache_file = Path(cache_file)
        elif self.usuario:
            self.cache_file = Path("data/users") / self.usuario / "cache.json"
        else:
            self.cache_file = Path("data/cache.json")

    def get(self, key: str):
        if not self.cache_file.exists():
            return None
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

        entry = data.get(key)
        if entry is None:
            return None
        timestamp, value = entry
        if self.ttl is not None and self.ttl > 0:
            if time.time() - timestamp >= self.ttl:
                return None  # expirado
        return value

    def set(self, key: str, value):
        data = {}
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                data = {}

        data[key] = [time.time(), value]
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def limpiar_expirados(self):
        """Elimina todas las entradas cuyo TTL ya venció."""
        if not self.cache_file.exists() or self.ttl is None or self.ttl <= 0:
            return
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return

        ahora = time.time()
        data = {k: v for k, v in data.items() if ahora - v[0] < self.ttl}
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def invalidar(self, key: str):
        """Fuerza que una clave se elimine del caché."""
        if not self.cache_file.exists():
            return
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return

        if key in data:
            del data[key]
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
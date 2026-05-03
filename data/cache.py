import json
import time
from pathlib import Path


class Cache:
    def __init__(self, cache_file: str = "data/cache.json", ttl: int = 3600):
        self.cache_file = Path(cache_file)
        self.ttl = ttl

    def get(self, key: str):
        if not self.cache_file.exists():
            return None
        with open(self.cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        entry = data.get(key)
        if entry is None:
            return None
        timestamp, value = entry
        if time.time() - timestamp < self.ttl:
            return value
        return None  # expirado

    def set(self, key: str, value):
        data = {}
        if self.cache_file.exists():
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        data[key] = [time.time(), value]
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def limpiar_expirados(self):
        """Elimina todas las entradas cuyo TTL ya venció."""
        if not self.cache_file.exists():
            return
        with open(self.cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        ahora = time.time()
        data = {k: v for k, v in data.items() if ahora - v[0] < self.ttl}
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def invalidar(self, key: str):
        """Fuerza que una clave se considere expirada en el próximo get."""
        if not self.cache_file.exists():
            return
        with open(self.cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if key in data:
            del data[key]
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
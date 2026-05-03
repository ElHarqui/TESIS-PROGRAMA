# Cache: guardar JSON local con TTL

import json
import time
from pathlib import Path


class Cache:
    def __init__(self, cache_file: str = "cache.json", ttl: int = 3600):  # 1 hora por defecto
        self.cache_file = Path(cache_file)
        self.ttl = ttl

    def get(self, key: str):
        if not self.cache_file.exists():
            return None
        with open(self.cache_file, 'r') as f:
            data = json.load(f)
        if key in data:
            timestamp, value = data[key]
            if time.time() - timestamp < self.ttl:
                return value
        return None

    def set(self, key: str, value):
        data = {}
        if self.cache_file.exists():
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
        data[key] = (time.time(), value)
        with open(self.cache_file, 'w') as f:
            json.dump(data, f)

    # TODO: limpiar entradas expiradas
import time
from pathlib import Path

from data.cache import Cache, sanitizar_usuario
from fitness.contexto import PreferenciasHorario
from fitness.preferencias import (
    cargar_preferencias_horarios,
    cargar_scores_docentes,
    guardar_preferencias_horarios,
    guardar_scores_docentes,
    resolver_ruta_preferencias,
)


class TestSanitizarUsuario:
    def test_usuario_normal(self):
        assert sanitizar_usuario("22200033") == "22200033"

    def test_usuario_con_espacios(self):
        assert sanitizar_usuario("  22200033  ") == "22200033"

    def test_usuario_caracteres_especiales(self):
        # Evita path traversal o caracteres inválidos en filenames
        sanitizado = sanitizar_usuario("alumno/../hack:123")
        assert "/" not in sanitizado
        assert ".." not in sanitizado
        assert ":" not in sanitizado

    def test_usuario_vacio(self):
        assert sanitizar_usuario("") == ""
        assert sanitizar_usuario(None) == ""


class TestCacheUserIsolation:
    def test_aislamiento_entre_usuarios(self, tmp_path):
        cache_a_file = tmp_path / "users" / "user_a" / "cache.json"
        cache_b_file = tmp_path / "users" / "user_b" / "cache.json"

        cache_a = Cache(cache_file=str(cache_a_file), ttl=3600)
        cache_b = Cache(cache_file=str(cache_b_file), ttl=3600)

        cache_a.set("datos_sum", {"alumno": "Juan Pérez", "codigo": "user_a"})

        # User B no debe ver la data de User A
        assert cache_b.get("datos_sum") is None

        # User A sí recupera sus datos
        data_a = cache_a.get("datos_sum")
        assert data_a is not None
        assert data_a["codigo"] == "user_a"

    def test_cache_ttl_expirado_y_no_expirado(self, tmp_path):
        cache_file = tmp_path / "cache_ttl.json"
        cache = Cache(cache_file=str(cache_file), ttl=1)

        cache.set("key_rapida", "valor1")
        assert cache.get("key_rapida") == "valor1"

        # Simular paso del tiempo
        time.sleep(1.1)
        assert cache.get("key_rapida") is None

    def test_cache_ttl_cero_o_none_no_expira(self, tmp_path):
        cache_file = tmp_path / "cache_no_expira.json"
        cache = Cache(cache_file=str(cache_file), ttl=0)

        cache.set("constante", "duradero")
        assert cache.get("constante") == "duradero"

    def test_limpiar_expirados_e_invalidar(self, tmp_path):
        cache_file = tmp_path / "cache_clean.json"
        cache = Cache(cache_file=str(cache_file), ttl=1)

        cache.set("item1", "v1")
        time.sleep(1.1)
        cache.limpiar_expirados()

        # Ya vencido y limpiado
        assert cache.get("item1") is None

        cache_largo = Cache(cache_file=str(cache_file), ttl=3600)
        cache_largo.set("item2", "v2")
        assert cache_largo.get("item2") == "v2"

        cache_largo.invalidar("item2")
        assert cache_largo.get("item2") is None


class TestPreferenciasUserIsolation:
    def test_aislamiento_scores_docentes(self, tmp_path, monkeypatch):
        # Redirigir data/users a tmp_path
        def mock_resolver(tipo, usuario_o_path=None, *, usuario=None, path=None):
            if path:
                return Path(path)
            u = usuario or usuario_o_path
            if u:
                return tmp_path / "users" / u / f"preferencias_{tipo}.json"
            return tmp_path / f"preferencias_{tipo}.json"

        monkeypatch.setattr("fitness.preferencias.resolver_ruta_preferencias", mock_resolver)

        # Usuario A guarda scores
        guardar_scores_docentes({"09756A": 0.2, "0A0690": 0.9}, usuario="alumnoA")

        # Usuario B carga scores: debe estar vacío (no ve alumnoA)
        scores_b = cargar_scores_docentes(usuario="alumnoB")
        assert scores_b == {}

        # Usuario A recupera sus scores
        scores_a = cargar_scores_docentes(usuario="alumnoA")
        assert scores_a.get("09756A") == 0.2
        assert scores_a.get("0A0690") == 0.9

    def test_aislamiento_preferencias_horarios(self, tmp_path, monkeypatch):
        def mock_resolver(tipo, usuario_o_path=None, *, usuario=None, path=None):
            if path:
                return Path(path)
            u = usuario or usuario_o_path
            if u:
                return tmp_path / "users" / u / f"preferencias_{tipo}.json"
            return tmp_path / f"preferencias_{tipo}.json"

        monkeypatch.setattr("fitness.preferencias.resolver_ruta_preferencias", mock_resolver)

        prefs_a = PreferenciasHorario(
            turno_preferido="noche",
            dias_libres_deseados=["VIERNES"],
            densidad="compacto",
            dias_libres_obligatorios=["SABADO"],
            hora_min="14:00",
        )
        guardar_preferencias_horarios(prefs_a, usuario="alumnoA")

        # Alumno B carga: debe obtener defaults ("indiferente", sin dias obligatorios)
        prefs_b = cargar_preferencias_horarios(usuario="alumnoB")
        assert prefs_b.turno_preferido == "indiferente"
        assert prefs_b.dias_libres_deseados == []
        assert prefs_b.dias_libres_obligatorios == []
        assert prefs_b.hora_min is None

        # Alumno A recupera sus preferencias intactas
        recuperadas_a = cargar_preferencias_horarios(usuario="alumnoA")
        assert recuperadas_a.turno_preferido == "noche"
        assert recuperadas_a.dias_libres_deseados == ["VIERNES"]
        assert recuperadas_a.dias_libres_obligatorios == ["SABADO"]
        assert recuperadas_a.hora_min == "14:00"


class TestGACachePersistence:
    def test_guardar_y_restaurar_ga_en_cache(self, monkeypatch, tmp_path):
        import streamlit as st
        from app import _guardar_cache_ga, _restaurar_cache_ga
        from models import Cromosoma, Seccion, BloqueHorario
        from services.optimizer_service import ResultadoOptimizacion

        orig_init = Cache.__init__
        def mock_cache_init(self, cache_file=None, usuario=None, ttl=None):
            orig_init(self, cache_file=cache_file, usuario=usuario, ttl=ttl)
            if usuario:
                self.cache_file = tmp_path / "users" / self.usuario / "cache.json"

        monkeypatch.setattr(Cache, "__init__", mock_cache_init)

        b = BloqueHorario("C1", 1, "DOC1", 1, "LUNES", "08:00", "10:00", "A1", "T", "TEORIA")
        s = Seccion(7, "C1", "Curso 1", 4.0, 1, "DOC1", "JUAN", "PEREZ", "GARCIA", 30, 10, [b])
        cromo = Cromosoma([s])

        res = ResultadoOptimizacion(
            horarios=[cromo],
            fitness_fin=[0.85],
            omitidas=[],
            duracion=1.23,
            gen_validos_ini=5,
            gen_validos_fin=45,
            modo_fallback=False,
            hard_relajadas=[],
            contexto_original=None,
            historial_convergencia=[{"generacion": 1, "mejor": 0.85, "promedio": 0.5, "validos": 45}],
        )

        _guardar_cache_ga("alumno1", res)

        # Simular nueva sesión con secciones cargadas pero sin horarios en RAM
        st.session_state["secciones"] = [s]
        st.session_state["horarios"] = None
        st.session_state["historial_convergencia"] = []

        ok = _restaurar_cache_ga("alumno1")
        assert ok is True
        assert st.session_state.horarios is not None
        assert len(st.session_state.horarios) == 1
        assert st.session_state.horarios[0].secciones[0].codAsignatura == "C1"
        assert len(st.session_state.historial_convergencia) == 1
        assert st.session_state.historial_convergencia[0]["mejor"] == 0.85

        # Otro alumno no debe restaurar horarios del primero
        st.session_state["horarios"] = None
        ok_otro = _restaurar_cache_ga("alumno2")
        assert ok_otro is False
        assert st.session_state.horarios is None

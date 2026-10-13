import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from data.exceptions import (
    SumCredencialesInvalidasError,
    SumDatosIncompletosError,
    SumError,
    SumMantenimientoError,
    SumTimeoutError,
)
from data.scraper import _fetch_all_parallel, obtener_datos_sum


@pytest.fixture
def anyio_backend():
    return "asyncio"


class TestSumExceptionsHierarchy:
    def test_todas_las_excepciones_heredan_de_sum_error(self):
        for exc in [
            SumCredencialesInvalidasError,
            SumMantenimientoError,
            SumTimeoutError,
            SumDatosIncompletosError,
        ]:
            assert issubclass(exc, SumError)
            assert issubclass(exc, Exception)


class TestScraperValidations:
    @pytest.mark.anyio
    async def test_credenciales_vacias_lanzan_error_inmediato(self):
        with pytest.raises(SumCredencialesInvalidasError) as exc_info:
            await obtener_datos_sum("", "")
        assert "no pueden estar vacíos" in str(exc_info.value)

    @pytest.mark.anyio
    async def test_fetch_all_parallel_exito(self):
        mock_page = MagicMock()
        mock_page.evaluate = AsyncMock(return_value=[
            {"key": "programacion", "ok": True, "data": {"secciones": []}, "status": 200},
            {"key": "prematricula", "ok": True, "data": {"cursos": []}, "status": 200},
            {"key": "alumno", "ok": True, "data": {"nombre": "Test"}, "status": 200},
            {"key": "plan_estudios", "ok": True, "data": {"ciclos": []}, "status": 200},
            {"key": "historial", "ok": True, "data": {"notas": []}, "status": 200},
        ])

        res = await _fetch_all_parallel(mock_page, {"p": "url"})
        assert res["programacion"] == {"secciones": []}
        assert res["prematricula"] == {"cursos": []}
        assert res["alumno"] == {"nombre": "Test"}
        assert len(res["errores"]) == 0

    @pytest.mark.anyio
    async def test_fetch_all_parallel_con_servidor_caido_lanza_mantenimiento(self):
        mock_page = MagicMock()
        mock_page.evaluate = AsyncMock(return_value=[
            {"key": "programacion", "ok": False, "status": 503, "error": "Service Unavailable"},
            {"key": "prematricula", "ok": False, "status": 503, "error": "Service Unavailable"},
            {"key": "alumno", "ok": False, "status": 502, "error": "Bad Gateway"},
            {"key": "plan_estudios", "ok": False, "status": 500, "error": "Internal Error"},
            {"key": "historial", "ok": False, "status": 503, "error": "Service Unavailable"},
        ])

        with pytest.raises(SumMantenimientoError) as exc_info:
            await _fetch_all_parallel(mock_page, {"p": "url"})
        assert "5xx" in str(exc_info.value)

    @pytest.mark.anyio
    async def test_fetch_all_parallel_captura_fallos_parciales(self):
        mock_page = MagicMock()
        mock_page.evaluate = AsyncMock(return_value=[
            {"key": "programacion", "ok": True, "data": {"secciones": []}, "status": 200},
            {"key": "prematricula", "ok": True, "data": {"cursos": []}, "status": 200},
            {"key": "alumno", "ok": True, "data": {"nombre": "Test"}, "status": 200},
            {"key": "plan_estudios", "ok": False, "status": 404, "error": "Not Found"},
            {"key": "historial", "ok": True, "data": {"notas": []}, "status": 200},
        ])

        res = await _fetch_all_parallel(mock_page, {"p": "url"})
        assert res["programacion"] is not None
        assert res["plan_estudios"] is None
        assert "plan_estudios" in res["errores"]


class TestScraperE2EFlowMock:
    @pytest.mark.anyio
    async def test_error_login_detectado_lanza_credenciales_invalidas(self):
        mock_resp = MagicMock(status=200)
        mock_page = MagicMock()
        mock_page.goto = AsyncMock(return_value=mock_resp)
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.fill = AsyncMock()
        mock_page.click = AsyncMock()
        mock_page.url = "https://sum.unmsm.edu.pe/alumnoWebSum/login"
        mock_page.content = AsyncMock(return_value="<div>Usuario o contraseña incorrecta</div>")
        mock_page.wait_for_url = AsyncMock(side_effect=Exception("Timeout"))
        mock_page.wait_for_selector = AsyncMock(return_value=None)

        mock_context = MagicMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)

        mock_browser = MagicMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        with patch("data.scraper.async_playwright") as mock_ap:
            mock_ap.return_value.__aenter__.return_value = mock_playwright
            with pytest.raises(SumCredencialesInvalidasError):
                await obtener_datos_sum(
                    "usuario_malo",
                    "clave_mala",
                    headless=True,
                    timeout_login_ms=50,
                    timeout_fetch_ms=50,
                )

    @pytest.mark.anyio
    async def test_datos_incompletos_si_falta_programacion(self):
        mock_resp = MagicMock(status=200)
        mock_page = MagicMock()
        mock_page.goto = AsyncMock(return_value=mock_resp)
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.fill = AsyncMock()
        mock_page.click = AsyncMock()
        mock_page.url = "https://sum.unmsm.edu.pe/alumnoWebSum/v2/inicio"
        mock_page.wait_for_url = AsyncMock(return_value=None)
        mock_page.wait_for_selector = AsyncMock(return_value=None)

        mock_context = MagicMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)

        mock_browser = MagicMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)
        mock_browser.close = AsyncMock()

        mock_playwright = MagicMock()
        mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

        with patch("data.scraper.async_playwright") as mock_ap:
            mock_ap.return_value.__aenter__.return_value = mock_playwright
            with patch("data.scraper._fetch_all_parallel") as mock_fetch:
                mock_fetch.return_value = {
                    "programacion": None,
                    "prematricula": {"cursos": []},
                    "alumno": {"nombre": "Test"},
                    "plan_estudios": None,
                    "historial": None,
                    "errores": ["programacion"],
                }
                with pytest.raises(SumDatosIncompletosError) as exc_info:
                    await obtener_datos_sum(
                        "22200033",
                        "clave123",
                        headless=True,
                        timeout_login_ms=50,
                        timeout_fetch_ms=50,
                    )
                assert "programación" in str(exc_info.value)

"""Tests unitarios para SummarizationService."""

import pytest
from unittest.mock import MagicMock

from src.services.summarization_service import SummarizationService


@pytest.fixture
def mock_summ_model():
    model = MagicMock()
    model.summarize.return_value = "este es el resumen generado"
    return model


@pytest.fixture
def service(mock_summ_model):
    return SummarizationService(summ_model=mock_summ_model)


# ─── Validación de entrada ────────────────────────────────────────────────────

def test_summarize_texto_vacio_raises_value_error(service):
    """Texto vacío debe lanzar ValueError."""
    with pytest.raises(ValueError, match="texto no puede estar vacío"):
        service.summarize(texto="")


def test_summarize_texto_solo_espacios_raises_value_error(service):
    """Texto de solo espacios debe lanzar ValueError."""
    with pytest.raises(ValueError, match="texto no puede estar vacío"):
        service.summarize(texto="   ")


def test_summarize_none_raises(service):
    """texto=None debe lanzar un error."""
    with pytest.raises((ValueError, AttributeError, TypeError)):
        service.summarize(texto=None)


# ─── Comportamiento correcto ──────────────────────────────────────────────────

def test_summarize_devuelve_tupla_str_float(service):
    """summarize() debe retornar una tupla (str, float)."""
    resumen, elapsed = service.summarize(texto="Un texto largo para resumir en español.")

    assert isinstance(resumen, str)
    assert isinstance(elapsed, float)
    assert resumen == "este es el resumen generado"
    assert elapsed >= 0


def test_summarize_llama_al_modelo(service, mock_summ_model):
    """summarize() debe llamar al modelo con el texto correcto."""
    texto = "El río Amazonas es el más largo del mundo."
    service.summarize(texto=texto)

    mock_summ_model.summarize.assert_called_once()
    call_kwargs = mock_summ_model.summarize.call_args[1]
    assert call_kwargs["texto"] == texto


def test_summarize_parametros_por_defecto(service, mock_summ_model):
    """summarize() debe pasar parámetros correctos al modelo."""
    service.summarize(texto="Texto de prueba para summarización.")

    call_kwargs = mock_summ_model.summarize.call_args[1]
    assert call_kwargs["max_length"] == 512
    assert call_kwargs["max_new_tokens"] == 150
    assert call_kwargs["min_length"] == 30
    assert call_kwargs["num_beams"] == 4


def test_summarize_elapsed_es_float_positivo(service):
    """El tiempo de elapsed debe ser un float >= 0."""
    _, elapsed = service.summarize(texto="Texto de prueba.")

    assert isinstance(elapsed, float)
    assert elapsed >= 0


# ─── Manejo de errores ────────────────────────────────────────────────────────

def test_summarize_propagates_model_exception(service, mock_summ_model):
    """Excepciones del modelo deben propagarse al llamador."""
    mock_summ_model.summarize.side_effect = RuntimeError("modelo no disponible")

    with pytest.raises(RuntimeError, match="modelo no disponible"):
        service.summarize(texto="Texto válido para resumir.")

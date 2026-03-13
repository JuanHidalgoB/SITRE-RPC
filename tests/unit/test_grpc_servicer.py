"""Tests unitarios para SitreServicer."""

import pytest
from unittest.mock import MagicMock

from src.grpc_servicer import SitreServicer


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_model_loader():
    loader = MagicMock()
    loader.get_asr_model.return_value = MagicMock()
    loader.get_summarization_model.return_value = MagicMock()
    return loader


@pytest.fixture
def mock_storage():
    storage = MagicMock()
    storage.save.return_value = "abc12345"
    return storage


@pytest.fixture
def mock_tracker():
    return MagicMock()


@pytest.fixture
def servicer(mock_model_loader, mock_storage, mock_tracker):
    """Crea un SitreServicer con servicios completamente mockeados."""
    svc = SitreServicer(mock_model_loader, mock_storage, mock_tracker)
    # Reemplazar los servicios internos con mocks
    svc.transcription_svc = MagicMock()
    svc.summarization_svc = MagicMock()
    return svc


@pytest.fixture
def grpc_context():
    return MagicMock()


# ─── RPC Transcribir ──────────────────────────────────────────────────────────

def test_transcribir_exito(servicer, grpc_context):
    """Transcribir debe retornar transcripcion y elapsed_s."""
    servicer.transcription_svc.transcribe.return_value = ("hola mundo", 1.2)

    request = MagicMock()
    request.audio = b"fake_audio"
    request.formato = "mp3"
    request.idioma = "es"

    response = servicer.Transcribir(request, grpc_context)

    assert response.transcripcion == "hola mundo"
    assert response.elapsed_s == pytest.approx(1.2, rel=1e-5)
    assert response.error == ""


def test_transcribir_error_retorna_campo_error(servicer, grpc_context):
    """Si falla la transcripción, debe retornar campo error poblado."""
    servicer.transcription_svc.transcribe.side_effect = RuntimeError("audio inválido")

    request = MagicMock()
    request.audio = b"bad_audio"
    request.formato = "mp3"
    request.idioma = "es"

    response = servicer.Transcribir(request, grpc_context)

    assert "audio inválido" in response.error
    assert response.transcripcion == ""


def test_transcribir_usa_idioma_por_defecto(servicer, grpc_context):
    """Si idioma está vacío, debe usar 'es' por defecto."""
    servicer.transcription_svc.transcribe.return_value = ("texto", 0.5)

    request = MagicMock()
    request.audio = b"audio"
    request.formato = "wav"
    request.idioma = ""

    servicer.Transcribir(request, grpc_context)

    call_kwargs = servicer.transcription_svc.transcribe.call_args[1]
    assert call_kwargs["language"] == "es"


# ─── RPC Resumir ──────────────────────────────────────────────────────────────

def test_resumir_exito(servicer, grpc_context):
    """Resumir debe retornar resumen y elapsed_s."""
    servicer.summarization_svc.summarize.return_value = ("resumen generado", 2.1)

    request = MagicMock()
    request.texto = "texto largo para resumir"

    response = servicer.Resumir(request, grpc_context)

    assert response.resumen == "resumen generado"
    assert response.elapsed_s == pytest.approx(2.1, rel=1e-5)
    assert response.error == ""


def test_resumir_error_retorna_campo_error(servicer, grpc_context):
    """Si falla la summarización, debe retornar campo error poblado."""
    servicer.summarization_svc.summarize.side_effect = ValueError("texto vacío")

    request = MagicMock()
    request.texto = ""

    response = servicer.Resumir(request, grpc_context)

    assert "texto vacío" in response.error
    assert response.resumen == ""


# ─── RPC Procesar ─────────────────────────────────────────────────────────────

def test_procesar_exito(servicer, mock_storage, grpc_context):
    """Procesar debe retornar transcripcion, resumen y tiempos."""
    servicer.transcription_svc.transcribe.return_value = ("texto completo", 3.0)
    servicer.summarization_svc.summarize.return_value = ("resumen conciso", 1.5)

    request = MagicMock()
    request.audio = b"audio_data"
    request.formato = "mp3"
    request.idioma = "es"

    response = servicer.Procesar(request, grpc_context)

    assert response.transcripcion == "texto completo"
    assert response.resumen == "resumen conciso"
    assert response.elapsed_asr == 3.0
    assert response.elapsed_sum == 1.5
    assert response.error == ""


def test_procesar_guarda_en_storage(servicer, mock_storage, grpc_context):
    """Procesar debe llamar a storage.save() con los resultados."""
    servicer.transcription_svc.transcribe.return_value = ("texto", 2.0)
    servicer.summarization_svc.summarize.return_value = ("resumen", 1.0)

    request = MagicMock()
    request.audio = b"audio"
    request.formato = "wav"
    request.idioma = "es"

    servicer.Procesar(request, grpc_context)

    mock_storage.save.assert_called_once_with("texto", "resumen", 2.0, 1.0)


def test_procesar_registra_mlflow(servicer, mock_tracker, grpc_context):
    """Procesar debe llamar al tracker MLflow con las métricas correctas."""
    servicer.transcription_svc.transcribe.return_value = ("texto", 1.5)
    servicer.summarization_svc.summarize.return_value = ("resumen", 0.8)

    request = MagicMock()
    request.audio = b"audio"
    request.formato = "mp3"
    request.idioma = "es"

    servicer.Procesar(request, grpc_context)

    mock_tracker.log_procesar.assert_called_once()
    call_kwargs = mock_tracker.log_procesar.call_args[1]
    assert call_kwargs["elapsed_asr"] == 1.5
    assert call_kwargs["elapsed_sum"] == 0.8


def test_procesar_error_retorna_campo_error(servicer, grpc_context):
    """Si falla la transcripción, Procesar debe retornar campo error."""
    servicer.transcription_svc.transcribe.side_effect = Exception("fallo crítico")

    request = MagicMock()
    request.audio = b"audio"
    request.formato = "mp3"
    request.idioma = "es"

    response = servicer.Procesar(request, grpc_context)

    assert "fallo crítico" in response.error
    assert response.transcripcion == ""
    assert response.resumen == ""

"""Tests unitarios para TranscriptionService."""

import pytest
from unittest.mock import MagicMock, patch

from src.services.transcription_service import TranscriptionService


@pytest.fixture
def mock_asr_model():
    model = MagicMock()
    model.transcribe.return_value = "hola mundo desde whisper"
    return model


@pytest.fixture
def service(mock_asr_model):
    return TranscriptionService(asr_model=mock_asr_model)


# ─── Validación de entrada ────────────────────────────────────────────────────

def test_transcribe_empty_bytes_raises_value_error(service):
    """Bytes vacíos deben lanzar ValueError."""
    with pytest.raises(ValueError, match="audio_bytes no puede estar vacío"):
        service.transcribe(audio_bytes=b"")


def test_transcribe_none_bytes_raises_value_error(service):
    """bytes=None debe lanzar ValueError."""
    with pytest.raises((ValueError, TypeError)):
        service.transcribe(audio_bytes=None)


# ─── Comportamiento correcto ──────────────────────────────────────────────────

def test_transcribe_devuelve_texto_y_elapsed(service):
    """transcribe() debe retornar una tupla (str, float)."""
    with patch.object(service, "_transcribe_file", return_value=("hola mundo", 1.5)):
        texto, elapsed = service.transcribe(audio_bytes=b"fake_audio", format="mp3")

    assert texto == "hola mundo"
    assert elapsed == 1.5


def test_transcribe_llama_transcribe_file(service):
    """transcribe() debe delegar al método _transcribe_file."""
    with patch.object(service, "_transcribe_file", return_value=("texto", 0.8)) as mock_tf:
        service.transcribe(audio_bytes=b"audio_data", format="wav", language="en")

    mock_tf.assert_called_once()
    _, lang = mock_tf.call_args[0]
    assert lang == "en"


def test_transcribe_idioma_por_defecto_es(service):
    """El idioma por defecto debe ser 'es'."""
    with patch.object(service, "_transcribe_file", return_value=("texto", 0.5)) as mock_tf:
        service.transcribe(audio_bytes=b"audio")

    _, lang = mock_tf.call_args[0]
    assert lang == "es"


def test_transcribe_extension_usa_formato(service):
    """El archivo temporal debe crearse con la extensión correcta."""
    creado_con = []

    original = __import__("tempfile").NamedTemporaryFile

    def fake_tmpfile(**kwargs):
        creado_con.append(kwargs.get("suffix", ""))
        return original(suffix=kwargs.get("suffix", ""), delete=kwargs.get("delete", True))

    with patch("tempfile.NamedTemporaryFile", side_effect=fake_tmpfile):
        with patch.object(service, "_transcribe_file", return_value=("t", 0.1)):
            service.transcribe(audio_bytes=b"audio", format="flac")

    assert creado_con[0] == ".flac"


# ─── Manejo de errores ────────────────────────────────────────────────────────

def test_transcribe_propagates_model_exception(service, mock_asr_model):
    """Errores del modelo deben propagarse al llamador."""
    import numpy as np

    mock_asr_model.transcribe.side_effect = RuntimeError("modelo falló")
    fake_audio = np.zeros(16000, dtype="float32")

    with patch("whisper.load_audio", return_value=fake_audio):
        with pytest.raises(RuntimeError, match="modelo falló"):
            service._transcribe_file("/fake/audio.mp3", language="es")

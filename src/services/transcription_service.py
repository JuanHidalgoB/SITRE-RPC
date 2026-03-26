"""Servicio de transcripción de audio.

Proporciona la lógica de negocio para convertir audio a texto usando ASR.
"""

import logging
import tempfile
import time
from pathlib import Path

from ..models import WhisperASRModel

log = logging.getLogger(__name__)


class TranscriptionService:
    """Servicio de transcripción de audio.

    Encapsula la lógica de transcripción, manejo de archivos temporales
    y métricas de rendimiento.

    Attributes:
        asr_model: Instancia del modelo Whisper.
    """

    def __init__(self, asr_model: WhisperASRModel):
        """Inicializa el servicio de transcripción.

        Args:
            asr_model: Modelo ASR a usar para transcripción.
        """
        self.asr_model = asr_model

    def transcribe(
        self,
        audio_bytes: bytes,
        format: str = "mp3",
        language: str = "es",
    ) -> tuple[str, float]:
        """Transcribe audio desde bytes.

        Args:
            audio_bytes: Contenido del archivo de audio en bytes.
            format: Formato del audio ('mp3', 'wav', 'flac', etc).
            language: Código de idioma ISO 639-1.

        Returns:
            Tupla (texto_transcrito, tiempo_transcripcion_segundos).

        Raises:
            ValueError: Si los bytes están vacíos o son inválidos.
            Exception: Si ocurre error en la transcripción.
        """
        if not audio_bytes:
            raise ValueError("audio_bytes no puede estar vacío")

        ext = f".{format}" if format else ".mp3"

        # Crear archivo temporal para almacenar el audio
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        try:
            return self._transcribe_file(tmp_path, language)
        finally:
            # Limpiar archivo temporal
            Path(tmp_path).unlink(missing_ok=True)

    def _transcribe_file(self, file_path: str, language: str = "es") -> tuple[str, float]:
        """Transcribe un archivo de audio desde disco.

        Args:
            file_path: Ruta al archivo de audio.
            language: Código de idioma ISO 639-1.

        Returns:
            Tupla (texto_transcrito, tiempo_transcripcion_segundos).

        Raises:
            Exception: Si ocurre error en libros o Whisper.
        """
        import whisper as _whisper

        log.info(f"Transcribiendo archivo: {file_path}")

        # Cargar audio con whisper.load_audio para garantizar compatibilidad en CPU
        audio = _whisper.load_audio(file_path)

        t0 = time.time()

        try:
            # Transcribir usando el modelo ASR
            texto = self.asr_model.transcribe(
                audio=audio,
                language=language,
                verbose=False,
            )

            elapsed = round(time.time() - t0, 2)
            log.info(f"✓ Transcripción completada: {len(texto)} caracteres en {elapsed}s")

            return texto, elapsed

        except Exception as e:
            log.error(f"Error en transcripción: {e}")
            raise

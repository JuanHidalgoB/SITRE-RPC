"""Módulo de gestión del modelo ASR (Automatic Speech Recognition).

Proporciona interfaz para cargar y utilizar el modelo Whisper de OpenAI
en dispositivos CPU.
"""

import logging
import time

log = logging.getLogger(__name__)


class WhisperASRModel:
    """Wrapper para el modelo Whisper de OpenAI.

    Attributes:
        model: Instancia cargada del modelo Whisper.
        device: Dispositivo de ejecución ('cpu' o 'cuda').
    """

    def __init__(self, model, device: str = "cpu"):
        """Inicializa el modelo ASR.

        Args:
            model: Modelo de Whisper ya cargado.
            device: Dispositivo a usar. Por defecto 'cpu'.
        """
        self.model = model
        self.device = device

    @classmethod
    def load(cls, model_name: str = "small", device: str = "cpu") -> "WhisperASRModel":
        """Carga el modelo Whisper desde HuggingFace.

        Args:
            model_name: Tamaño del modelo ('tiny', 'small', 'medium', etc).
            device: Dispositivo ('cpu' o 'cuda').

        Returns:
            Instancia de WhisperASRModel lista para usar.

        Raises:
            ImportError: Si el módulo whisper no está disponible.
        """
        import whisper

        log.info(f"Cargando modelo Whisper-{model_name}...")
        t0 = time.time()

        model = whisper.load_model(model_name, device=device)

        elapsed = time.time() - t0
        log.info(f"Whisper-{model_name} cargado en {elapsed:.1f}s")

        return cls(model, device)

    def transcribe(self, audio, language: str = "es", verbose: bool = False) -> str:
        """Transcribe audio usando Whisper.

        Args:
            audio: Array numpy de audio a 16kHz o ruta a archivo.
            language: Código de idioma ISO 639-1 ('es', 'en', etc).
            verbose: Si mostrar progreso durante la transcripción.

        Returns:
            Texto transcrito.

        Raises:
            Exception: Si ocurre error durante la transcripción.
        """
        try:
            result = self.model.transcribe(
                audio=audio,
                language=language,
                verbose=verbose,
                fp16=False,
            )
            return result["text"].strip()
        except Exception as e:
            log.error(f"Error en transcripción: {e}")
            raise

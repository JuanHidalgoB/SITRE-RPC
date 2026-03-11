"""Módulos de modelos de ML.

Contiene clases y funciones para cargar y gestionar modelos de:
- ASR (Automatic Speech Recognition) con Whisper
- Summarization con mT5
"""

from .asr_model import WhisperASRModel
from .summarization_model import MT5SummarizationModel
from .model_loader import ModelLoader

__all__ = ["WhisperASRModel", "MT5SummarizationModel", "ModelLoader"]

"""Módulo centralizado para carga de modelos.

Proporciona una clase que gestiona la carga de todos los modelos necesarios
para el pipeline de SITRE (Transcripción + Resumen).
"""

import logging
import time

import torch

from .asr_model import WhisperASRModel
from .summarization_model import MT5SummarizationModel

log = logging.getLogger(__name__)


class ModelLoader:
    """Cargador centralizado de modelos.

    Gestiona la carga de modelos ASR y Summarization, proporcionando
    una interfaz única para inicializar todo el pipeline.

    Attributes:
        asr_model: Instancia de WhisperASRModel.
        summ_model: Instancia de MT5SummarizationModel.
    """

    def __init__(self, asr_model: WhisperASRModel, summ_model: MT5SummarizationModel):
        """Inicializa el cargador con modelos ya cargados.

        Args:
            asr_model: Modelo de transcripción.
            summ_model: Modelo de summarización.
        """
        self.asr_model = asr_model
        self.summ_model = summ_model

    @classmethod
    def load_all(
        cls,
        whisper_size: str = "small",
        mt5_model: str = "ELiRF/mt5-base-dacsa-es",
        device: str = "cpu",
        dtype=torch.float32,
    ) -> "ModelLoader":
        """Carga todos los modelos del pipeline.

        Args:
            whisper_size: Tamaño del modelo Whisper.
            mt5_model: Nombre del modelo mT5.
            device: Dispositivo de ejecución ('cpu' o 'cuda').
            dtype: Precisión numérica para mT5.

        Returns:
            Instancia de ModelLoader con todos los modelos cargados.
        """
        log.info("═" * 60)
        log.info("Iniciando carga de modelos...")
        log.info("═" * 60)

        log.info(f"Dispositivo: {device.upper()} | Threads: {torch.get_num_threads()}")

        t_start = time.time()

        # Cargar ASR
        log.info("[1/2] Whisper...")
        asr = WhisperASRModel.load(model_name=whisper_size, device=device)

        # Cargar Summarization
        log.info("[2/2] mT5...")
        summ = MT5SummarizationModel.load(model_name=mt5_model, dtype=dtype)

        total_time = time.time() - t_start
        log.info("═" * 60)
        log.info(f"✓ Todos los modelos cargados en {total_time:.1f}s")
        log.info("═" * 60)

        return cls(asr, summ)

    def get_asr_model(self) -> WhisperASRModel:
        """Obtiene el modelo ASR.

        Returns:
            Instancia de WhisperASRModel.
        """
        return self.asr_model

    def get_summarization_model(self) -> MT5SummarizationModel:
        """Obtiene el modelo de summarización.

        Returns:
            Instancia de MT5SummarizationModel.
        """
        return self.summ_model

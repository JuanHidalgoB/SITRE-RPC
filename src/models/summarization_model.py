"""Módulo de gestión del modelo de Summarization.

Proporciona interfaz para cargar y utilizar el modelo mT5 especializado
en generación de resúmenes en español.
"""

import logging
import time

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

log = logging.getLogger(__name__)


class MT5SummarizationModel:
    """Wrapper para el modelo mT5 de generación de resúmenes.

    Attributes:
        model: Instancia del modelo mT5 cargado.
        tokenizer: Tokenizador correspondiente al modelo.
        dtype: Tipo de dato para cálculos (torch.float32, etc).
    """

    def __init__(self, model, tokenizer, dtype=torch.float32):
        """Inicializa el modelo de summarización.

        Args:
            model: Modelo de Seq2Seq ya cargado.
            tokenizer: Tokenizador del modelo.
            dtype: Tipo de dato ('torch.float32', 'torch.float16', etc).
        """
        self.model = model
        self.tokenizer = tokenizer
        self.dtype = dtype

    @classmethod
    def load(
        cls,
        model_name: str = "ELiRF/mt5-base-dacsa-es",
        dtype=torch.float32,
    ) -> "MT5SummarizationModel":
        """Carga el modelo mT5 desde HuggingFace.

        Args:
            model_name: Identificador del modelo en HuggingFace Hub.
            dtype: Precisión numérica del modelo.

        Returns:
            Instancia de MT5SummarizationModel lista para usar.

        Raises:
            Exception: Si falla la descarga o carga del modelo.
        """
        log.info(f"Cargando {model_name}...")
        t0 = time.time()

        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            dtype=dtype,
            low_cpu_mem_usage=True,
        )

        # Corregir embeddings faltantes — en mT5 comparten pesos con shared
        shared = model.shared.weight.data
        model.encoder.embed_tokens.weight.data.copy_(shared)
        model.decoder.embed_tokens.weight.data.copy_(shared)

        elapsed = time.time() - t0
        log.info(f"{model_name} cargado en {elapsed:.1f}s")

        return cls(model, tokenizer, dtype)

    def summarize(
        self,
        texto: str,
        max_length: int = 512,
        max_new_tokens: int = 150,
        min_length: int = 30,
        num_beams: int = 4,
    ) -> str:
        """Genera resumen del texto usando mT5.

        Args:
            texto: Texto a resumir.
            max_length: Longitud máxima de entrada al tokenizador.
            max_new_tokens: Máximo de tokens nuevos a generar.
            min_length: Longitud mínima del resumen.
            num_beams: Número de beams para búsqueda (beam search).

        Returns:
            Texto del resumen generado.

        Raises:
            Exception: Si ocurre error durante la generación.
        """
        try:
            inputs = self.tokenizer(
                texto,
                return_tensors="pt",
                max_length=max_length,
                truncation=True,
            )

            with torch.no_grad():
                ids = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    min_length=min_length,
                    num_beams=num_beams,
                    early_stopping=True,
                    no_repeat_ngram_size=3,
                )

            return self.tokenizer.decode(ids[0], skip_special_tokens=True)
        except Exception as e:
            log.error(f"Error en summarización: {e}")
            raise

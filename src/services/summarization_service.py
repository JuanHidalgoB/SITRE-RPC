"""Servicio de generación de resúmenes.

Proporciona la lógica de negocio para generar resúmenes de texto
usando modelos de Seq2Seq.
"""

import logging
import time

from ..models import MT5SummarizationModel

log = logging.getLogger(__name__)


class SummarizationService:
    """Servicio de generación de resúmenes.

    Encapsula la lógica para generar resúmenes de texto,
    incluyendo métricas de rendimiento.

    Attributes:
        summ_model: Instancia del modelo de summarización.
    """

    def __init__(self, summ_model: MT5SummarizationModel):
        """Inicializa el servicio de summarización.

        Args:
            summ_model: Modelo de summarización a usar.
        """
        self.summ_model = summ_model

    def summarize(
        self,
        texto: str,
        max_length: int = 512,
        max_new_tokens: int = 150,
        min_length: int = 30,
        num_beams: int = 4,
    ) -> tuple[str, float]:
        """Genera un resumen del texto.

        Args:
            texto: Texto a resumir.
            max_length: Longitud máxima de entrada.
            max_new_tokens: Máximo de tokens nuevos a generar.
            min_length: Longitud mínima del resumen.
            num_beams: Número de beams para beam search.

        Returns:
            Tupla (texto_resumen, tiempo_generacion_segundos).

        Raises:
            ValueError: Si el texto está vacío.
            Exception: Si ocurre error en la generación.
        """
        if not texto or not texto.strip():
            raise ValueError("texto no puede estar vacío")

        log.info(f"Generando resumen para texto de {len(texto)} caracteres...")

        t0 = time.time()

        try:
            # Generar resumen usando el modelo
            resumen = self.summ_model.summarize(
                texto=texto,
                max_length=max_length,
                max_new_tokens=max_new_tokens,
                min_length=min_length,
                num_beams=num_beams,
            )

            elapsed = round(time.time() - t0, 2)
            log.info(f"✓ Resumen generado: {len(resumen)} caracteres en {elapsed}s")

            return resumen, elapsed

        except Exception as e:
            log.error(f"Error en summarización: {e}")
            raise

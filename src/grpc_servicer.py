"""Implementación del servicio gRPC.

Contiene el servicer que implementa los endpoints RPC definidos en el proto.
El tracking de métricas se realiza automáticamente con MLflow.
"""

import logging

import sitre_pb2
import sitre_pb2_grpc

from src.config import MT5_MODEL, WHISPER_SIZE
from src.models import ModelLoader
from src.services import SummarizationService, TranscriptionService
from src.storage import ResultsStorage
from src.tracking import MLflowTracker

log = logging.getLogger(__name__)


class SitreServicer(sitre_pb2_grpc.SitreServiceServicer):
    """Implementación del servicio SITRE.

    Implementa los endpoints RPC para transcripción, summarización
    y pipeline completo. Registra métricas en MLflow por cada llamada.

    Attributes:
        transcription_svc: Servicio de transcripción.
        summarization_svc: Servicio de summarización.
        storage: Sistema de almacenamiento de resultados.
        tracker: Tracker de métricas MLflow.
    """

    def __init__(
        self,
        model_loader: ModelLoader,
        storage: ResultsStorage,
        tracker: MLflowTracker | None = None,
    ):
        """Inicializa el servicer.

        Args:
            model_loader: Instancia de ModelLoader con modelos cargados.
            storage: Sistema de almacenamiento de resultados.
            tracker: Tracker MLflow (opcional; se crea uno por defecto si no se pasa).
        """
        self.transcription_svc = TranscriptionService(model_loader.get_asr_model())
        self.summarization_svc = SummarizationService(model_loader.get_summarization_model())
        self.storage = storage
        self.tracker = tracker if tracker is not None else MLflowTracker()
        log.info("✓ Servicer SITRE inicializado")

    def Transcribir(self, request, context):
        """RPC Transcribir: Convierte audio a texto.

        Args:
            request: AudioRequest con audio y metadatos.
            context: Contexto gRPC.

        Returns:
            TranscripcionResponse con texto y tiempo de ejecución.
        """
        log.info("└─ RPC: Transcribir")
        try:
            texto, elapsed = self.transcription_svc.transcribe(
                audio_bytes=request.audio,
                format=request.formato,
                language=request.idioma or "es",
            )

            log.info(f"   └─ Resultado: {len(texto)} chars en {elapsed}s")

            self.tracker.log_transcribir(
                formato=request.formato,
                idioma=request.idioma or "es",
                elapsed_s=elapsed,
                transcripcion_len=len(texto),
            )

            return sitre_pb2.TranscripcionResponse(
                transcripcion=texto,
                elapsed_s=elapsed,
            )

        except Exception as e:
            log.error(f"   └─ Error: {e}")
            return sitre_pb2.TranscripcionResponse(error=str(e))

    def Resumir(self, request, context):
        """RPC Resumir: Genera resumen de texto.

        Args:
            request: TextoRequest con texto a resumir.
            context: Contexto gRPC.

        Returns:
            ResumenResponse con resumen y tiempo de ejecución.
        """
        log.info("└─ RPC: Resumir")
        try:
            resumen, elapsed = self.summarization_svc.summarize(texto=request.texto)

            log.info(f"   └─ Resultado: {len(resumen)} chars en {elapsed}s")

            self.tracker.log_resumir(
                elapsed_s=elapsed,
                texto_len=len(request.texto),
                resumen_len=len(resumen),
            )

            return sitre_pb2.ResumenResponse(
                resumen=resumen,
                elapsed_s=elapsed,
            )

        except Exception as e:
            log.error(f"   └─ Error: {e}")
            return sitre_pb2.ResumenResponse(error=str(e))

    def Procesar(self, request, context):
        """RPC Procesar: Pipeline completo (audio → transcripción → resumen).

        Args:
            request: AudioRequest con audio.
            context: Contexto gRPC.

        Returns:
            ProcesarResponse con transcripción, resumen y tiempos.
        """
        log.info("└─ RPC: Procesar (pipeline completo)")
        try:
            # Transcribir
            texto, e_asr = self.transcription_svc.transcribe(
                audio_bytes=request.audio,
                format=request.formato,
                language=request.idioma or "es",
            )

            # Resumir
            resumen, e_sum = self.summarization_svc.summarize(texto=texto)

            # Guardar en almacenamiento
            result_id = self.storage.save(texto, resumen, e_asr, e_sum)

            log.info(f"   └─ Completado: ASR={e_asr}s | SUM={e_sum}s | ID={result_id}")

            # Registrar métricas en MLflow
            self.tracker.log_procesar(
                formato=request.formato,
                idioma=request.idioma or "es",
                elapsed_asr=e_asr,
                elapsed_sum=e_sum,
                transcripcion_len=len(texto),
                resumen_len=len(resumen),
                whisper_size=WHISPER_SIZE,
                mt5_model=MT5_MODEL,
            )

            return sitre_pb2.ProcesarResponse(
                transcripcion=texto,
                resumen=resumen,
                elapsed_asr=e_asr,
                elapsed_sum=e_sum,
            )

        except Exception as e:
            log.error(f"   └─ Error: {e}")
            return sitre_pb2.ProcesarResponse(error=str(e))

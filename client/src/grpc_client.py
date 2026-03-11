"""Cliente gRPC para SITRE.

Proporciona interfaz simplificada para consumir los servicios SITRE
desde el cliente Streamlit.
"""

import logging
import sys
from pathlib import Path
from typing import NamedTuple

import grpc

# Agregar generated al path para importar módulos proto
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_GENERATED_PATH = str(_PROJECT_ROOT / "generated")
if _GENERATED_PATH not in sys.path:
    sys.path.insert(0, _GENERATED_PATH)

try:
    import sitre_pb2
    import sitre_pb2_grpc
except ImportError as e:
    raise ImportError(
        f"No se pudo importar módulos proto. ¿Ejecutaste 'make setup'?\n"
        f"Error: {e}"
    ) from e

log = logging.getLogger(__name__)


class TranscripcionResponse(NamedTuple):
    """Respuesta de transcripción.

    Attributes:
        texto: Texto transcrito.
        elapsed_s: Tiempo de ejecución en segundos.
        error: Mensaje de error, o None si fue exitoso.
    """

    texto: str
    elapsed_s: float
    error: str | None = None


class ResumenResponse(NamedTuple):
    """Respuesta de resumen.

    Attributes:
        resumen: Texto del resumen.
        elapsed_s: Tiempo de ejecución en segundos.
        error: Mensaje de error, o None si fue exitoso.
    """

    resumen: str
    elapsed_s: float
    error: str | None = None


class ProcesarResponse(NamedTuple):
    """Respuesta del pipeline completo.

    Attributes:
        transcripcion: Texto transcrito.
        resumen: Texto del resumen.
        elapsed_asr: Tiempo de transcripción en segundos.
        elapsed_sum: Tiempo de resumen en segundos.
        error: Mensaje de error, o None si fue exitoso.
    """

    transcripcion: str
    resumen: str
    elapsed_asr: float
    elapsed_sum: float
    error: str | None = None


class SitreClient:
    """Cliente para conectarse al servidor SITRE-RPC.

    Proporciona métodos para llamar a los RPC del servidor de forma simplificada.

    Attributes:
        server_addr: Dirección del servidor (ej: 'localhost:50051').
        stub: Stub del servicio gRPC.
        channel: Canal gRPC establecido.
    """

    def __init__(self, server_addr: str = "localhost:50051"):
        """Inicializa el cliente.

        Args:
            server_addr: Dirección del servidor gRPC.

        Raises:
            grpc.RpcError: Si no puede conectarse al servidor.
        """
        self.server_addr = server_addr
        self._setup_channel()

    def _setup_channel(self):
        """Configura el canal gRPC con opciones personalizadas."""
        MB = 1024 * 1024
        options = [
            ("grpc.max_receive_message_length", 100 * MB),
            ("grpc.max_send_message_length", 100 * MB),
        ]
        self.channel = grpc.insecure_channel(self.server_addr, options=options)
        self.stub = sitre_pb2_grpc.SitreServiceStub(self.channel)
        log.info(f"Cliente conectado a {self.server_addr}")

    def procesar_audio(
        self,
        audio_bytes: bytes,
        formato: str = "mp3",
        idioma: str = "spanish",
        timeout: int = 2400,
    ) -> ProcesarResponse:
        """Ejecuta el pipeline completo (audio → transcripción → resumen).

        Args:
            audio_bytes: Contenido del archivo de audio en bytes.
            formato: Formato del audio ('mp3', 'wav', etc).
            idioma: Idioma del audio.
            timeout: Timeout en segundos.

        Returns:
            ProcesarResponse con transcripción, resumen y tiempos.

        Raises:
            grpc.RpcError: Si hay error en la comunicación.
            ValueError: Si los parámetros son inválidos.
        """
        if not audio_bytes:
            raise ValueError("audio_bytes no puede estar vacío")

        try:
            request = sitre_pb2.AudioRequest(
                audio=audio_bytes,
                formato=formato,
                idioma=idioma,
            )
            response = self.stub.Procesar(request, timeout=timeout)

            if response.error:
                return ProcesarResponse(
                    transcripcion="",
                    resumen="",
                    elapsed_asr=0.0,
                    elapsed_sum=0.0,
                    error=response.error,
                )

            return ProcesarResponse(
                transcripcion=response.transcripcion,
                resumen=response.resumen,
                elapsed_asr=response.elapsed_asr,
                elapsed_sum=response.elapsed_sum,
            )

        except grpc.RpcError as e:
            log.error(f"Error gRPC: {e.code()}: {e.details()}")
            raise

    def transcribir(
        self,
        audio_bytes: bytes,
        formato: str = "mp3",
        idioma: str = "spanish",
        timeout: int = 1200,
    ) -> TranscripcionResponse:
        """Transcribe audio a texto.

        Args:
            audio_bytes: Contenido del archivo de audio en bytes.
            formato: Formato del audio.
            idioma: Idioma del audio.
            timeout: Timeout en segundos.

        Returns:
            TranscripcionResponse con texto transcrito y tiempo.

        Raises:
            grpc.RpcError: Si hay error en la comunicación.
            ValueError: Si los parámetros son inválidos.
        """
        if not audio_bytes:
            raise ValueError("audio_bytes no puede estar vacío")

        try:
            request = sitre_pb2.AudioRequest(
                audio=audio_bytes,
                formato=formato,
                idioma=idioma,
            )
            response = self.stub.Transcribir(request, timeout=timeout)

            if response.error:
                return TranscripcionResponse(
                    texto="",
                    elapsed_s=0.0,
                    error=response.error,
                )

            return TranscripcionResponse(
                texto=response.transcripcion,
                elapsed_s=response.elapsed_s,
            )

        except grpc.RpcError as e:
            log.error(f"Error gRPC: {e.code()}: {e.details()}")
            raise

    def resumir(
        self,
        texto: str,
        timeout: int = 120,
    ) -> ResumenResponse:
        """Genera un resumen de texto.

        Args:
            texto: Texto a resumir.
            timeout: Timeout en segundos.

        Returns:
            ResumenResponse con resumen y tiempo.

        Raises:
            grpc.RpcError: Si hay error en la comunicación.
            ValueError: Si el texto está vacío.
        """
        if not texto or not texto.strip():
            raise ValueError("texto no puede estar vacío")

        try:
            request = sitre_pb2.TextoRequest(texto=texto.strip())
            response = self.stub.Resumir(request, timeout=timeout)

            if response.error:
                return ResumenResponse(
                    resumen="",
                    elapsed_s=0.0,
                    error=response.error,
                )

            return ResumenResponse(
                resumen=response.resumen,
                elapsed_s=response.elapsed_s,
            )

        except grpc.RpcError as e:
            log.error(f"Error gRPC: {e.code()}: {e.details()}")
            raise

    def close(self):
        """Cierra la conexión gRPC."""
        if hasattr(self, "channel"):
            self.channel.close()
            log.info("Conexión cerrada")

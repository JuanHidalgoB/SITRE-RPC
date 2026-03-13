"""SITRE-RPC — Servidor gRPC.

Servidor que orquesta los servicios de transcripción y summarización.
Optimizado para CPU usando threading con gRPC.
"""

import signal
import sys
import threading
from pathlib import Path

# PRIMERO: Agregar proyecto root al path ANTES de cualquier otro import
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# SEGUNDO: Agregar generated al path
_GENERATED_PATH = str(_PROJECT_ROOT / "generated")
if _GENERATED_PATH not in sys.path:
    sys.path.insert(0, _GENERATED_PATH)

# Ahora importar el resto
import logging
from concurrent import futures

import grpc
import torch

import sitre_pb2_grpc
from src.config import DEVICE, HOST, MAX_MESSAGE_MB, MAX_WORKERS, PORT, WHISPER_SIZE, MT5_MODEL
from src.grpc_servicer import SitreServicer
from src.models import ModelLoader
from src.storage import ResultsStorage
from src.tracking import MLflowTracker

DTYPE = torch.float32

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ─── Inicialización ───────────────────────────────────────────────────────────


def main():
    """Punto de entrada del servidor.

    Carga los modelos, configura el almacenamiento e inicia el servidor gRPC.
    """
    log.info("")
    log.info("╔══════════════════════════════════════════════════════════════╗")
    log.info("║                      SITRE-RPC SERVER                        ║")
    log.info("╚══════════════════════════════════════════════════════════════╝")
    log.info("")

    try:
        # Cargar modelos
        model_loader = ModelLoader.load_all(
            whisper_size=WHISPER_SIZE,
            mt5_model=MT5_MODEL,
            device=DEVICE,
            dtype=DTYPE,
        )

        # Configurar almacenamiento
        storage = ResultsStorage(_PROJECT_ROOT / "resultados")

        # Configurar tracker MLflow
        tracker = MLflowTracker()
        tracker.register_models(
            whisper_size=WHISPER_SIZE,
            mt5_model=MT5_MODEL,
            device=DEVICE,
            load_time_s=model_loader.load_time_s,
        )

        # Crear servicer
        servicer = SitreServicer(model_loader, storage, tracker)

        # Configurar gRPC
        MB = 1024 * 1024
        options = [
            ("grpc.max_receive_message_length", MAX_MESSAGE_MB * MB),
            ("grpc.max_send_message_length", MAX_MESSAGE_MB * MB),
        ]

        server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=MAX_WORKERS),
            options=options,
        )
        sitre_pb2_grpc.add_SitreServiceServicer_to_server(servicer, server)
        server.add_insecure_port(f"{HOST}:{PORT}")

        log.info("")
        log.info(f"◆ Host:    {HOST}")
        log.info(f"◆ Puerto:  {PORT}")
        log.info(f"◆ Workers: {MAX_WORKERS}")
        log.info(f"◆ Threads: {torch.get_num_threads()}")
        log.info("")
        log.info("Iniciando servidor...")
        log.info("")

        server.start()

        log.info("━" * 62)
        log.info("✓ El servidor está escuchando...")
        log.info("━" * 62)
        log.info("")

        # Manejar Ctrl+C limpiamente (evita access violation en Windows)
        stop_event = threading.Event()

        def _on_sigint(_signum, _frame):
            stop_event.set()

        signal.signal(signal.SIGINT, _on_sigint)
        stop_event.wait()

        log.info("")
        log.info("━" * 62)
        log.info("⊘ Apagando servidor (Ctrl+C)...")
        log.warning("  Finalizando conexiones...")
        server.stop(grace=5).wait()
        log.info("✓ Servidor detenido")
        log.info("━" * 62)
        log.info("")

    except Exception as e:
        log.error("")
        log.error("✗ Error fatal:")
        log.error(f"  {e}")
        log.error("")
        raise


if __name__ == "__main__":
    main()

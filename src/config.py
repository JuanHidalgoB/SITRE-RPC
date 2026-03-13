"""Configuración centralizada de SITRE-RPC.

Todas las constantes del sistema se definen aquí para evitar
valores hardcodeados dispersos en el código.
"""

# ─── Servidor gRPC ────────────────────────────────────────────────────────────
HOST = "0.0.0.0"
PORT = 50051
MAX_WORKERS = 4
MAX_MESSAGE_MB = 100

# ─── Modelos ──────────────────────────────────────────────────────────────────
WHISPER_SIZE = "small"
MT5_MODEL = "ELiRF/mt5-base-dacsa-es"
DEVICE = "cpu"

# ─── MLflow ───────────────────────────────────────────────────────────────────
MLFLOW_EXPERIMENT = "sitre-rpc-inference"
MLFLOW_TRACKING_URI = "sqlite:///mlflow.db"

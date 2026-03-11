"""Módulo cliente de SITRE."""

from .grpc_client import SitreClient, ProcesarResponse, ResumenResponse, TranscripcionResponse

__all__ = [
    "SitreClient",
    "ProcesarResponse",
    "ResumenResponse",
    "TranscripcionResponse",
]

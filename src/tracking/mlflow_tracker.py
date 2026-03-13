"""Tracking de métricas de inferencia con MLflow.

Registra cada llamada al pipeline Procesar como un run de MLflow,
incluyendo parámetros de entrada y métricas de rendimiento.
"""

import logging

import mlflow
from mlflow.tracking import MlflowClient

from src.config import MLFLOW_EXPERIMENT, MLFLOW_TRACKING_URI

log = logging.getLogger(__name__)


class MLflowTracker:
    """Gestiona el tracking de experimentos MLflow para SITRE-RPC.

    Registra parámetros y métricas de cada ejecución del pipeline
    de transcripción y summarización.

    Attributes:
        experiment_name: Nombre del experimento en MLflow.
        enabled: Si el tracking está activo.
    """

    def __init__(
        self,
        experiment_name: str = MLFLOW_EXPERIMENT,
        tracking_uri: str = MLFLOW_TRACKING_URI,
    ):
        """Inicializa el tracker y configura el experimento MLflow.

        Args:
            experiment_name: Nombre del experimento en MLflow.
            tracking_uri: URI de almacenamiento de MLflow (local o remoto).
        """
        self.experiment_name = experiment_name
        self.enabled = False

        try:
            mlflow.set_tracking_uri(tracking_uri)
            mlflow.set_experiment(experiment_name)
            self.enabled = True
            log.info(f"✓ MLflow configurado: experimento='{experiment_name}' uri='{tracking_uri}'")
        except Exception as e:
            log.warning(f"MLflow no disponible (tracking deshabilitado): {e}")

    def log_procesar(
        self,
        formato: str,
        idioma: str,
        elapsed_asr: float,
        elapsed_sum: float,
        transcripcion_len: int,
        resumen_len: int,
        whisper_size: str = "",
        mt5_model: str = "",
    ) -> None:
        """Registra una ejecución del RPC Procesar en MLflow.

        Args:
            formato: Formato del audio procesado ('mp3', 'wav', etc).
            idioma: Idioma del audio ('es', 'en', etc).
            elapsed_asr: Tiempo de transcripción en segundos.
            elapsed_sum: Tiempo de summarización en segundos.
            transcripcion_len: Número de caracteres en la transcripción.
            resumen_len: Número de caracteres en el resumen.
            whisper_size: Tamaño del modelo Whisper usado.
            mt5_model: Nombre del modelo mT5 usado.
        """
        if not self.enabled:
            return

        try:
            with mlflow.start_run():
                mlflow.log_params(
                    {
                        "formato": formato,
                        "idioma": idioma,
                        "whisper_size": whisper_size,
                        "mt5_model": mt5_model,
                    }
                )
                mlflow.log_metrics(
                    {
                        "whisper_transcripcion_tiempo_s": elapsed_asr,
                        "mt5_resumen_tiempo_s": elapsed_sum,
                        "pipeline_total_tiempo_s": round(elapsed_asr + elapsed_sum, 2),
                        "whisper_output_caracteres": transcripcion_len,
                        "mt5_output_caracteres": resumen_len,
                    }
                )
        except Exception as e:
            log.warning(f"Error al registrar en MLflow (no crítico): {e}")

    def log_transcribir(
        self,
        formato: str,
        idioma: str,
        elapsed_s: float,
        transcripcion_len: int,
    ) -> None:
        """Registra una ejecución del RPC Transcribir en MLflow.

        Args:
            formato: Formato del audio.
            idioma: Idioma del audio.
            elapsed_s: Tiempo de transcripción en segundos.
            transcripcion_len: Número de caracteres transcritos.
        """
        if not self.enabled:
            return

        try:
            with mlflow.start_run():
                mlflow.log_params({"formato": formato, "idioma": idioma})
                mlflow.log_metrics(
                    {
                        "whisper_transcripcion_tiempo_s": elapsed_s,
                        "whisper_output_caracteres": transcripcion_len,
                    }
                )
        except Exception as e:
            log.warning(f"Error al registrar en MLflow (no crítico): {e}")

    def log_resumir(
        self,
        elapsed_s: float,
        texto_len: int,
        resumen_len: int,
    ) -> None:
        """Registra una ejecución del RPC Resumir en MLflow.

        Args:
            elapsed_s: Tiempo de generación del resumen en segundos.
            texto_len: Número de caracteres del texto de entrada.
            resumen_len: Número de caracteres del resumen generado.
        """
        if not self.enabled:
            return

        try:
            with mlflow.start_run():
                mlflow.log_metrics(
                    {
                        "mt5_resumen_tiempo_s": elapsed_s,
                        "mt5_input_caracteres": texto_len,
                        "mt5_output_caracteres": resumen_len,
                    }
                )
        except Exception as e:
            log.warning(f"Error al registrar en MLflow (no crítico): {e}")

    def register_models(
        self,
        whisper_size: str,
        mt5_model: str,
        device: str,
        load_time_s: float,
    ) -> None:
        """Registra los modelos cargados en el MLflow Model Registry.

        Crea un run de carga inicial con la configuración de los modelos
        y los registra en el Model Registry de MLflow para seguimiento
        de versiones.

        Args:
            whisper_size: Tamaño del modelo Whisper ('tiny', 'small', etc).
            mt5_model: Identificador HuggingFace del modelo mT5.
            device: Dispositivo de ejecución ('cpu' o 'cuda').
            load_time_s: Tiempo total de carga de ambos modelos en segundos.
        """
        if not self.enabled:
            return

        try:
            client = MlflowClient()

            # Run dedicado al registro de modelos
            with mlflow.start_run(run_name="registro-modelos") as run:
                mlflow.set_tag("tipo", "carga-inicial")
                mlflow.log_params(
                    {
                        "whisper_size": whisper_size,
                        "mt5_model": mt5_model,
                        "device": device,
                    }
                )
                mlflow.log_metric("modelos_carga_tiempo_s", round(load_time_s, 2))
                mlflow.log_dict(
                    {
                        "asr": {
                            "model_id": f"openai/whisper-{whisper_size}",
                            "task": "automatic-speech-recognition",
                            "language": "es",
                        },
                        "summarization": {
                            "model_id": mt5_model,
                            "task": "summarization",
                            "language": "es",
                        },
                        "device": device,
                        "load_time_s": round(load_time_s, 2),
                    },
                    "model_config.json",
                )
                run_id = run.info.run_id

            # Registrar en el Model Registry
            modelos = [
                (
                    "sitre-whisper-asr",
                    f"Whisper-{whisper_size} para transcripción de audio en español",
                ),
                (
                    "sitre-mt5-summarization",
                    f"{mt5_model} para resumen ejecutivo en español",
                ),
            ]
            for nombre, descripcion in modelos:
                try:
                    client.create_registered_model(name=nombre, description=descripcion)
                except Exception:
                    pass  # El modelo ya existe en el registry; solo añadimos versión

                client.create_model_version(
                    name=nombre,
                    source=f"runs:/{run_id}/model_config.json",
                    run_id=run_id,
                    description=f"Cargado desde HuggingFace Hub. Device: {device}",
                )
                log.info(f"✓ Modelo registrado en MLflow Registry: {nombre}")

        except Exception as e:
            log.warning(f"Error al registrar modelos en MLflow (no crítico): {e}")

"""Módulo de almacenamiento de resultados.

Proporciona funcionalidad para guardar y recuperar resultados
de transcripción y resumen en formato JSON.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

log = logging.getLogger(__name__)


class ResultsStorage:
    """Sistema de almacenamiento de resultados.

    Gestiona la persistencia de resultados de procesamiento en formato JSON,
    con timestamps e IDs únicos para cada resultado.

    Attributes:
        storage_dir: Ruta al directorio donde se almacenan resultados.
    """

    def __init__(self, storage_dir: Path | str = "resultados"):
        """Inicializa el almacenamiento de resultados.

        Args:
            storage_dir: Directorio donde guardar resultados.
                        Se creará si no existe.
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        log.info(f"Almacenamiento configurado en: {self.storage_dir}")

    def save(
        self,
        transcripcion: str,
        resumen: str,
        elapsed_asr: float,
        elapsed_sum: float,
    ) -> str:
        """Guarda un resultado completo.

        Args:
            transcripcion: Texto transcrito.
            resumen: Texto del resumen.
            elapsed_asr: Tiempo de transcripción en segundos.
            elapsed_sum: Tiempo de summarización en segundos.

        Returns:
            ID único del resultado (primeros 8 caracteres del UUID).

        Raises:
            IOError: Si falla la escritura al disco.
        """
        result_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()

        data: Dict[str, Any] = {
            "id": result_id,
            "timestamp": timestamp,
            "transcripcion": transcripcion,
            "resumen": resumen,
            "elapsed_asr_s": elapsed_asr,
            "elapsed_sum_s": elapsed_sum,
            "total_s": elapsed_asr + elapsed_sum,
        }

        try:
            result_file = self.storage_dir / f"resultado_{result_id}.json"
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            log.info(f"✓ Resultado guardado: {result_file}")
            return result_id

        except IOError as e:
            log.error(f"Error al guardar resultado: {e}")
            raise

    def get_result(self, result_id: str) -> Dict[str, Any] | None:
        """Recupera un resultado por ID.

        Args:
            result_id: ID del resultado (primeros 8 caracteres del UUID).

        Returns:
            Diccionario con datos del resultado, o None si no existe.

        Raises:
            json.JSONDecodeError: Si el archivo JSON está corrupto.
        """
        result_file = self.storage_dir / f"resultado_{result_id}.json"

        if not result_file.exists():
            log.warning(f"Resultado no encontrado: {result_id}")
            return None

        try:
            with open(result_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            log.error(f"Error al leer resultado {result_id}: {e}")
            raise

    def list_results(self) -> list[Dict[str, Any]]:
        """Lista todos los resultados disponibles.

        Returns:
            Lista de diccionarios con datos de cada resultado.
        """
        results = []
        for result_file in sorted(self.storage_dir.glob("resultado_*.json")):
            try:
                with open(result_file, "r", encoding="utf-8") as f:
                    results.append(json.load(f))
            except json.JSONDecodeError as e:
                log.warning(f"Error al leer {result_file.name}: {e}")
                continue

        log.info(f"Se encontraron {len(results)} resultados")
        return results

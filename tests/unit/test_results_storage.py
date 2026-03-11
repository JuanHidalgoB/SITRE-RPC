"""Tests unitarios para ResultsStorage."""

import json
import pytest
from pathlib import Path

from src.storage.results_storage import ResultsStorage


@pytest.fixture
def storage(tmp_path):
    """Crea un ResultsStorage en un directorio temporal."""
    return ResultsStorage(storage_dir=tmp_path)


# ─── save() ──────────────────────────────────────────────────────────────────

def test_save_crea_archivo_json(storage, tmp_path):
    """save() debe crear un archivo resultado_*.json."""
    storage.save("texto de prueba", "resumen de prueba", 1.5, 2.3)

    archivos = list(tmp_path.glob("resultado_*.json"))
    assert len(archivos) == 1


def test_save_retorna_id_de_8_chars(storage):
    """save() debe retornar un ID de 8 caracteres."""
    result_id = storage.save("texto", "resumen", 1.0, 0.5)

    assert isinstance(result_id, str)
    assert len(result_id) == 8


def test_save_json_contiene_campos_correctos(storage, tmp_path):
    """El JSON guardado debe tener todos los campos esperados."""
    result_id = storage.save("mi transcripción", "mi resumen", 2.1, 1.8)

    archivo = tmp_path / f"resultado_{result_id}.json"
    data = json.loads(archivo.read_text(encoding="utf-8"))

    assert data["id"] == result_id
    assert data["transcripcion"] == "mi transcripción"
    assert data["resumen"] == "mi resumen"
    assert data["elapsed_asr_s"] == 2.1
    assert data["elapsed_sum_s"] == 1.8
    assert data["total_s"] == pytest.approx(2.1 + 1.8)
    assert "timestamp" in data


def test_save_ids_son_unicos(storage):
    """Cada llamada a save() debe generar un ID único."""
    id1 = storage.save("texto1", "resumen1", 1.0, 1.0)
    id2 = storage.save("texto2", "resumen2", 2.0, 2.0)
    id3 = storage.save("texto3", "resumen3", 3.0, 3.0)

    assert len({id1, id2, id3}) == 3


# ─── get_result() ─────────────────────────────────────────────────────────────

def test_get_result_retorna_datos_guardados(storage):
    """get_result() debe devolver los datos del resultado guardado."""
    result_id = storage.save("transcripción", "resumen", 1.0, 0.5)
    data = storage.get_result(result_id)

    assert data is not None
    assert data["id"] == result_id
    assert data["transcripcion"] == "transcripción"
    assert data["resumen"] == "resumen"


def test_get_result_devuelve_none_si_no_existe(storage):
    """get_result() debe devolver None para un ID inexistente."""
    result = storage.get_result("noexiste")

    assert result is None


def test_get_result_json_corrupto_lanza_error(storage, tmp_path):
    """get_result() debe lanzar JSONDecodeError si el archivo está corrupto."""
    archivo = tmp_path / "resultado_xxxxxxxx.json"
    archivo.write_text("{ invalid json }", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        storage.get_result("xxxxxxxx")


# ─── list_results() ───────────────────────────────────────────────────────────

def test_list_results_vacio(storage):
    """list_results() debe retornar lista vacía si no hay resultados."""
    results = storage.list_results()

    assert results == []


def test_list_results_retorna_todos(storage):
    """list_results() debe retornar todos los resultados guardados."""
    storage.save("texto1", "resumen1", 1.0, 1.0)
    storage.save("texto2", "resumen2", 2.0, 2.0)
    storage.save("texto3", "resumen3", 3.0, 3.0)

    results = storage.list_results()

    assert len(results) == 3


def test_list_results_cada_item_tiene_campos(storage):
    """Cada item de list_results() debe tener los campos básicos."""
    storage.save("texto", "resumen", 1.5, 0.8)
    results = storage.list_results()

    assert len(results) == 1
    item = results[0]
    assert "id" in item
    assert "transcripcion" in item
    assert "resumen" in item
    assert "elapsed_asr_s" in item
    assert "elapsed_sum_s" in item
    assert "total_s" in item


# ─── Inicialización ───────────────────────────────────────────────────────────

def test_storage_crea_directorio_si_no_existe(tmp_path):
    """ResultsStorage debe crear el directorio si no existe."""
    nuevo_dir = tmp_path / "nuevo_subdir" / "resultados"
    assert not nuevo_dir.exists()

    ResultsStorage(storage_dir=nuevo_dir)

    assert nuevo_dir.exists()

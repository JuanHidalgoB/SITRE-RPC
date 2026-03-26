#!/usr/bin/env python3
"""
Script para ver los resultados procesados guardados en directorio resultados/
"""

import json
from pathlib import Path

RESULTADOS_DIR = Path(__file__).parent / "resultados"

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("📊 RESULTADOS GUARDADOS")
    print("=" * 80 + "\n")

    if not RESULTADOS_DIR.exists():
        print("❌ No hay directorio de resultados aún.")
        exit(1)

    archivos = sorted(RESULTADOS_DIR.glob("resultado_*.json"), reverse=True)

    if not archivos:
        print("❌ No hay resultados guardados.")
        exit(1)

    for i, archivo in enumerate(archivos, 1):
        with open(archivo, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"[{i}] ID: {data['id']}")
        print(f"    Timestamp: {data['timestamp']}")
        print(f"    Tiempo ASR: {data['elapsed_asr_s']}s")
        print(f"    Tiempo Resumen: {data['elapsed_sum_s']}s")
        print(f"    Tiempo Total: {data['total_s']}s")
        print(f"    Transcripción: {data['transcripcion'][:100]}...")
        print(f"    Resumen: {data['resumen'][:100]}...")
        print(f"    Archivo: {archivo}")
        print()

    print("=" * 80)
    print(f"Total de resultados: {len(archivos)}")
    print("=" * 80 + "\n")

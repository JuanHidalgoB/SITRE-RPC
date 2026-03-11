"""Configuración global de pytest para SITRE-RPC.

Agrega el proyecto root y generated/ al sys.path para que todos
los tests puedan importar los módulos correctamente.
"""

import sys
from pathlib import Path

# Raíz del proyecto (un nivel arriba de tests/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
GENERATED_PATH = PROJECT_ROOT / "generated"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(GENERATED_PATH) not in sys.path:
    sys.path.insert(0, str(GENERATED_PATH))

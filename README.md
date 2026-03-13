# SITRE-RPC

**Sistema de Transcripción y Resumen Ejecutivo** — pipeline distribuido de IA para transcribir audio en español y generar resúmenes ejecutivos, implementado con gRPC, Whisper y mT5.

> Tablero Kanban: https://github.com/users/JuanHidalgoB/projects/1

---

## Tecnologias

| Componente | Tecnologia |
|---|---|
| ASR (transcripcion) | `openai/whisper-small` (244M params) |
| Resumen | `ELiRF/mt5-base-dacsa-es` (~580M params) |
| Comunicacion | gRPC (Protocol Buffers) |
| Interfaz | Streamlit |
| Seguimiento ML | MLflow (SQLite backend) |
| Gestion de entorno | uv |

---

## Arquitectura

El sistema esta compuesto por dos servicios independientes que se comunican via gRPC:

```
┌─────────────────────────────────────────────────────┐
│  Cliente (Streamlit :8501)                          │
│  client/app.py  ←→  client/src/grpc_client.py       │
└──────────────────────┬──────────────────────────────┘
                       │  gRPC (puerto 50051)
┌──────────────────────▼──────────────────────────────┐
│  Servidor gRPC (:50051)                             │
│  server/main.py                                      │
│    ├── SitreServicer   (src/grpc_servicer.py)        │
│    ├── WhisperASRModel (src/models/)                 │
│    ├── MT5Summarization(src/models/)                 │
│    ├── ResultsStorage  (src/storage/)  → resultados/ │
│    └── MLflowTracker   (src/tracking/) → mlflow.db   │
└─────────────────────────────────────────────────────┘
```

### RPCs definidos en `proto/sitre.proto`

| RPC | Entrada | Salida | Descripcion |
|---|---|---|---|
| `Procesar` | `AudioRequest` | `ProcesarResponse` | Pipeline completo: audio → transcripcion → resumen |
| `Transcribir` | `AudioRequest` | `TranscripcionResponse` | Solo ASR |
| `Resumir` | `TextoRequest` | `ResumenResponse` | Solo resumen de texto |

---

## Estructura del proyecto

```
SITRE-RPC/
├── proto/
│   └── sitre.proto              # Definicion del servicio gRPC
├── generated/                   # Codigo auto-generado (make setup)
├── server/
│   └── main.py                  # Entrypoint del servidor gRPC
├── src/
│   ├── config.py                # Configuracion centralizada
│   ├── grpc_servicer.py         # Implementacion de los 3 RPCs
│   ├── models/
│   │   ├── asr_model.py         # Wrapper Whisper
│   │   ├── summarization_model.py # Wrapper mT5
│   │   └── model_loader.py      # Carga ambos modelos
│   ├── services/
│   │   ├── transcription_service.py
│   │   └── summarization_service.py
│   ├── storage/
│   │   └── results_storage.py   # Persiste resultados en JSON
│   └── tracking/
│       └── mlflow_tracker.py    # Tracking de experimentos y model registry
├── client/
│   ├── app.py                   # Interfaz Streamlit
│   └── src/grpc_client.py       # Cliente gRPC
├── tests/
│   └── unit/                    # 35 pruebas unitarias (pytest)
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── Makefile
```

---

## Instalacion y ejecucion local

### Requisitos previos

- Python 3.10+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- ffmpeg

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
winget install ffmpeg
```

### Inicio rapido

```bash
# 1. Clonar el repositorio
git clone https://github.com/JuanHidalgoB/SITRE-RPC.git
cd SITRE-RPC

# 2. Instalar dependencias y compilar proto
make setup

# 3. Terminal 1 - Servidor gRPC
make server

# 4. Terminal 2 - Cliente Streamlit
make client
```

Abrir http://localhost:8501 en el navegador.

### Comandos disponibles

```bash
make setup      # Instalar deps y compilar .proto
make server     # Servidor gRPC (puerto 50051)
make client     # Cliente Streamlit (puerto 8501)
make test       # Pruebas unitarias
make mlflow-ui  # Dashboard MLflow (puerto 5000)
make lint       # Revisar y formatear con Ruff
make kill       # Liberar puerto 50051
make clean      # Borrar generated/ y __pycache__
```

---

## Ejecucion con Docker

```bash
# Construir y levantar ambos servicios
docker-compose up --build

# En segundo plano
docker-compose up --build -d

# Detener
docker-compose down
```

| Servicio | Puerto | URL |
|---|---|---|
| Servidor gRPC | 50051 | — |
| Cliente Streamlit | 8501 | http://localhost:8501 |

Los datos persisten en volumenes Docker: `resultados/`, `mlruns/` y cache de modelos HuggingFace.

---

## MLflow

El servidor registra automaticamente cada inferencia y los modelos en el MLflow Model Registry.

```bash
# Ver dashboard (requiere que el servidor haya corrido al menos una vez)
make mlflow-ui
# Abrir http://localhost:5000
```

**Experimento:** `sitre-rpc-inference`

**Metricas registradas por RPC:**

| RPC | Metricas |
|---|---|
| Procesar | `whisper_transcripcion_tiempo_s`, `mt5_resumen_tiempo_s`, `pipeline_total_tiempo_s`, `whisper_output_caracteres`, `mt5_output_caracteres` |
| Transcribir | `whisper_transcripcion_tiempo_s`, `whisper_output_caracteres` |
| Resumir | `mt5_resumen_tiempo_s`, `mt5_input_caracteres`, `mt5_output_caracteres` |

**Modelos registrados:** `sitre-whisper-asr`, `sitre-mt5-summarization`

---

## Pruebas

```bash
make test
# 35 tests, 0 failures
```

Cobertura: servicer gRPC, almacenamiento de resultados, servicio de transcripcion y servicio de resumen.
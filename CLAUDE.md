# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**SITRE-RPC** (Sistema de Transcripción y Resumen Ejecutivo) is a distributed audio transcription and summarization system using gRPC. It uses:
- **Whisper-small** (`openai/whisper-small`) for Spanish ASR
- **mT5-base-dacsa-es** (`ELiRF/mt5-base-dacsa-es`) for text summarization
- **gRPC** for server-client communication
- **Streamlit** for the web client UI

The system runs CPU-only (PyTorch CPU build from a custom index).

## Commands

**Package manager:** `uv` (not pip)

```bash
# Install dependencies and compile proto files (run first)
make setup

# Run server (gRPC on port 50051) — Terminal 1
make server

# Run client (Streamlit on port 8501) — Terminal 2
make client

# Stop server and free port 50051 (use before make server if port is busy)
make kill

# Run unit tests
make test

# View MLflow metrics dashboard (http://localhost:5000)
make mlflow-ui

# Lint and format (excludes generated/)
make lint

# View saved results
make resultados

# Clean venv and generated files
make clean
```

On Windows, server and client must be started in separate terminals — `make run` only prints instructions.

**Recompile proto manually:**
```bash
.venv/Scripts/python.exe -m grpc_tools.protoc -I proto --python_out=generated --grpc_python_out=generated proto/sitre.proto
```

## Architecture

```
PROYECTO3_SITRE/
├── proto/sitre.proto        # gRPC service definition (source of truth)
├── generated/               # Auto-generated pb2 files (do not edit)
├── server/main.py           # gRPC server entrypoint
├── src/                     # Server-side business logic
│   ├── grpc_servicer.py     # Implements the 3 RPC endpoints
│   ├── models/              # Model wrappers (WhisperASRModel, MT5SummarizationModel, ModelLoader)
│   ├── services/            # Business logic (TranscriptionService, SummarizationService)
│   └── storage/             # ResultsStorage — persists pipeline results as JSON in resultados/
├── client/
│   ├── app.py               # Streamlit UI entrypoint
│   └── src/grpc_client.py   # SitreClient wrapping the gRPC stub
└── resultados/              # JSON results from Procesar RPC (auto-created)
```

### RPC Service (proto/sitre.proto)

Three RPCs are defined:
- `Procesar(AudioRequest) → ProcesarResponse` — full pipeline: audio → transcription → summary (also saves to `resultados/`)
- `Transcribir(AudioRequest) → TranscripcionResponse` — ASR only
- `Resumir(TextoRequest) → ResumenResponse` — summarization only

### Server path resolution

`server/main.py` and `src/grpc_servicer.py` manually insert both the project root and `generated/` into `sys.path` at startup so that `sitre_pb2` and the `src` package resolve correctly. The same pattern is used in `client/src/grpc_client.py` (which resolves 3 levels up to the project root).

### Key configuration (server/main.py)

- `HOST = "0.0.0.0"`, `PORT = 50051`, `MAX_WORKERS = 4`, `DEVICE = "cpu"`, `DTYPE = torch.float32`
- gRPC max message size: 100 MB (for large audio files)
- Whisper model size: `"small"`, mT5 model: `"ELiRF/mt5-base-dacsa-es"`

### Storage

`ResultsStorage` writes `resultados/resultado_<8-char-uuid>.json` only for the `Procesar` RPC (not for `Transcribir` or `Resumir` alone). Use `make resultados` or `ver_resultados.py` to inspect saved results.

## Development Notes

- After modifying `proto/sitre.proto`, re-run `make setup` to regenerate `generated/sitre_pb2.py` and `generated/sitre_pb2_grpc.py`.
- The `generated/` directory must contain an `__init__.py` (created by `make setup`).
- Ruff is configured with `line-length = 100` and `target-version = "py310"`.
- Models are downloaded from Hugging Face on first run and cached locally; startup takes significantly longer on first launch.

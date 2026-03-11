# SITRE-RPC
**Sistema Distribuido de Transcripción y Resumen Ejecutivo en Español**

## Estructura

```
sitre-rpc/
├── proto/
│   └── sitre.proto       ← definición del servicio gRPC
├── server/
│   └── main.py           ← servidor gRPC + Whisper + mT5
├── client/
│   └── app.py            ← frontend Streamlit
├── generated/            ← código auto-generado (make setup)
├── pyproject.toml        ← dependencias compartidas
└── Makefile
```

## Requisitos previos

```bash
# uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# ffmpeg (para decodificación de audio)
sudo apt install ffmpeg
```

## Inicio rápido

```bash
# 1. Instalar todo (descarga ~1 GB de modelos la primera vez)
make setup

# 2. Levantar todo junto
make run

# O en terminales separadas:
make server   # gRPC en localhost:50051
make client   # Streamlit en http://localhost:8501
```

## Otros comandos

```bash
make kill       # Detener el servidor (libera el puerto 50051)
make test       # Ejecutar pruebas unitarias
make mlflow-ui  # Ver dashboard de métricas en http://localhost:5000
make resultados # Ver resultados guardados en resultados/
make lint       # Ruff: revisar y formatear código
make clean      # Borrar venv y archivos generados
```

> **Nota (Windows):** Si al hacer `make server` sale error de puerto ocupado,
> ejecuta `make kill` primero para liberar el puerto 50051.

## Modelos

| Rol | Modelo | Params |
|-----|--------|--------|
| ASR | `openai/whisper-tiny` | 39M |
| Resumen | `ELiRF/mt5-base-dacsa-es` | ~580M |

# ─────────────────────────────────────────────────────────────────────────────
#  SITRE-RPC — Makefile
#  Uso: make <comando>
# ─────────────────────────────────────────────────────────────────────────────

VENV    := .venv
PYTHON  := $(VENV)/bin/python
PROTO   := proto/sitre.proto
GEN     := generated

.PHONY: help setup server client run lint clean

# ─── help ─────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  SITRE-RPC — Comandos disponibles"
	@echo "  ─────────────────────────────────"
	@echo "  make setup   → Instalar deps y compilar .proto"
	@echo "  make server  → Levantar servidor gRPC  (puerto 50051)"
	@echo "  make client  → Levantar cliente Streamlit (puerto 8501)"
	@echo "  make run     → Levantar server + client juntos"
	@echo "  make lint    → Revisar y formatear código con Ruff"
	@echo "  make clean   → Borrar venv, cache y archivos generados"
	@echo ""

# ─── setup ────────────────────────────────────────────────────────────────────
setup:
	@echo ""
	@echo "━━━ [1/2] Instalando dependencias ━━━"
	uv sync
	@echo ""
	@echo "━━━ [2/2] Compilando proto → generated/ ━━━"
	mkdir -p $(GEN)
	$(PYTHON) -m grpc_tools.protoc \
		-I proto \
		--python_out=$(GEN) \
		--grpc_python_out=$(GEN) \
		$(PROTO)
	touch $(GEN)/__init__.py
	@echo ""
	@echo "  ✓ Todo listo. Ejecuta: make run"
	@echo ""

# ─── server ───────────────────────────────────────────────────────────────────
server:
	@echo "[server] gRPC escuchando en localhost:50051"
	$(PYTHON) server/main.py

# ─── client ───────────────────────────────────────────────────────────────────
client:
	@echo "[client] Streamlit en http://localhost:8501"
	$(VENV)/bin/streamlit run client/app.py \
		--server.port 8501 \
		--server.headless true

# ─── run ──────────────────────────────────────────────────────────────────────
run:
	@echo ""
	@echo "  Iniciando SITRE-RPC (Ctrl+C para detener todo)"
	@echo "  Server → localhost:50051"
	@echo "  Client → http://localhost:8501"
	@echo ""
	@trap 'kill 0' SIGINT; \
		$(MAKE) server & \
		sleep 20 && $(MAKE) client & \
		wait

# ─── lint ─────────────────────────────────────────────────────────────────────
lint:
	$(VENV)/bin/ruff check . --fix --exclude generated/
	$(VENV)/bin/ruff format .  --exclude generated/

# ─── clean ────────────────────────────────────────────────────────────────────
clean:
	rm -rf $(VENV) $(GEN)
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "[clean] ✓ Listo"

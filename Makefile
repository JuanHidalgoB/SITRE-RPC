# ─────────────────────────────────────────────────────────────────────────────
#  SITRE-RPC — Makefile
#  Uso: make <comando>
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
#  SITRE-RPC — Makefile
#  Uso: make <comando>
# ─────────────────────────────────────────────────────────────────────────────

VENV    := .venv
PROTO   := proto/sitre.proto
GEN     := generated

# Detectar SO y usar comandos correctos
ifeq ($(OS),Windows_NT)
    MKDIR   := if not exist $(GEN) mkdir $(GEN)
    PYTHON  := $(VENV)\Scripts\python.exe
else
    MKDIR   := mkdir -p $(GEN)
    PYTHON  := $(VENV)/bin/python
endif

.PHONY: help setup server client run test mlflow-ui lint clean resultados kill

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
	$(MKDIR)
	$(PYTHON) -m grpc_tools.protoc \
		-I proto \
		--python_out=$(GEN) \
		--grpc_python_out=$(GEN) \
		$(PROTO)
ifeq ($(OS),Windows_NT)
	type nul > $(GEN)\__init__.py
else
	touch $(GEN)/__init__.py
endif
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
ifeq ($(OS),Windows_NT)
	$(VENV)\Scripts\streamlit run client/app.py --server.port 8501 --server.headless true
else
	$(VENV)/bin/streamlit run client/app.py --server.port 8501 --server.headless true
endif

# ─── run ──────────────────────────────────────────────────────────────────────
ifndef OS
    UNAME_S := $(shell uname -s)
    ifeq ($(UNAME_S),Linux)
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
    endif
    ifeq ($(UNAME_S),Darwin)
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
    endif
else
    run:
	@echo ""
	@echo "  Iniciando SITRE-RPC (Ctrl+C para detener todo)"
	@echo "  Server → localhost:50051"
	@echo "  Client → http://localhost:8501"
	@echo ""
	@echo "  [IMPORTANTE] Abre DOS terminales:"
	@echo "    Terminal 1: make server"
	@echo "    Terminal 2: make client"
	@echo ""
endif

# ─── kill ─────────────────────────────────────────────────────────────────────
kill:
	@echo [kill] Liberando puerto 50051...
	-$(PYTHON) -c "import subprocess; o=subprocess.run('netstat -ano',shell=True,capture_output=True,text=True).stdout; pids={l.split()[-1] for l in o.splitlines() if ':50051' in l and l.split()[-1].isdigit()}; [subprocess.run('taskkill /F /PID '+p+' /T',shell=True) for p in pids]"
	@echo [kill] Listo

# ─── test ─────────────────────────────────────────────────────────────────────
test:
	$(PYTHON) -m pytest tests/ -v

# ─── mlflow-ui ────────────────────────────────────────────────────────────────
mlflow-ui:
	@echo "[mlflow] Dashboard en http://localhost:5000"
	$(PYTHON) -m mlflow ui --port 5000

# ─── lint ─────────────────────────────────────────────────────────────────────
lint:
	$(VENV)/bin/ruff check . --fix --exclude generated/
	$(VENV)/bin/ruff format .  --exclude generated/

# ─── resultados ───────────────────────────────────────────────────────────────
resultados:
	$(PYTHON) ver_resultados.py

# ─── clean ────────────────────────────────────────────────────────────────────
clean:
	rm -rf $(VENV) $(GEN)
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "[clean] ✓ Listo"

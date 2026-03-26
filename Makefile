# SITRE-RPC - Makefile

.PHONY: help setup server client test mlflow-ui lint clean resultados kill

help:
	@echo "  make setup      : Instalar deps y compilar .proto"
	@echo "  make server     : Servidor gRPC (puerto 50051)"
	@echo "  make client     : Cliente Streamlit (puerto 8501)"
	@echo "  make test       : Pruebas unitarias"
	@echo "  make mlflow-ui  : Dashboard MLflow (puerto 5000)"
	@echo "  make lint       : Revisar y formatear con Ruff"
	@echo "  make kill       : Liberar puerto 50051"
	@echo "  make clean      : Borrar generated/ y __pycache__"

setup:
	uv sync
	uv run python -c "import pathlib; pathlib.Path('generated').mkdir(exist_ok=True); pathlib.Path('generated/__init__.py').touch()"
	uv run python -m grpc_tools.protoc -I proto --python_out=generated --grpc_python_out=generated proto/sitre.proto
	@echo "Listo. Ejecuta: make server / make client"

server:
	uv run python server/main.py

client:
	uv run streamlit run client/app.py --server.port 8501 --server.headless true

kill:
	-uv run python -c "import subprocess; o=subprocess.run('netstat -ano',shell=True,capture_output=True,text=True).stdout; pids={l.split()[-1] for l in o.splitlines() if ':50051' in l and l.split()[-1].isdigit()}; [subprocess.run('taskkill /F /PID '+p+' /T',shell=True) for p in pids]"

test:
	uv run pytest tests/ -v

mlflow-ui:
	uv run mlflow ui --port 5000 --backend-store-uri sqlite:///mlflow.db

lint:
	uv run ruff check . --fix --exclude generated/
	uv run ruff format . --exclude generated/

resultados:
	uv run python ver_resultados.py

clean:
	rm -rf generated
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

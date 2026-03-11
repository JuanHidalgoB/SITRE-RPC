"""ARQUITECTURA DE SITRE — Guía de Diseño.

Este documento describe la arquitectura del proyecto SITRE después de la
refactorización, enfatizando baja acoplación y alta cohesión.

═══════════════════════════════════════════════════════════════════════════════

PRINCIPIOS DE DISEÑO

1. Baja Acoplación (Loose Coupling)
   - Cada módulo es independiente y puede ser reemplazado fácilmente
   - Las dependencias son inyectadas (inyección de dependencias)
   - Interfaces claras entre componentes (ServiceRequester → Service)

2. Alta Cohesión (High Cohesion)
   - Cada módulo tiene una única responsabilidad bien definida
   - Código relacionado está agrupado en el mismo archivo/carpeta
   - Métodos/funciones trabajan juntos para un propósito común

═══════════════════════════════════════════════════════════════════════════════

ESTRUCTURA DE CARPETAS

PROYECTO3_SITRE/
├── src/                                  # Código principal reutilizable
│   ├── __init__.py
│   ├── models/                           # Capa de modelos
│   │   ├── __init__.py
│   │   ├── asr_model.py                  # Modelo Whisper (ASR)
│   │   ├── summarization_model.py        # Modelo mT5 (Summarization)
│   │   └── model_loader.py               # Orquestador de carga de modelos
│   ├── services/                         # Capa de servicios (lógica)
│   │   ├── __init__.py
│   │   ├── transcription_service.py      # Lógica de transcripción
│   │   └── summarization_service.py      # Lógica de resumen
│   ├── storage/                          # Capa de persistencia
│   │   ├── __init__.py
│   │   └── results_storage.py            # Guardado de resultados (JSON)
│   └── grpc_servicer.py                  # Servicer gRPC
├── server/
│   └── main.py                           # Punto de entrada del servidor
├── client/
│   ├── src/                              # Cliente como librería
│   │   ├── __init__.py
│   │   └── grpc_client.py                # Cliente gRPC encapsulado
│   └── app.py                            # UI Streamlit
├── proto/
│   └── sitre.proto                       # Definición de servicios gRPC
├── generated/                            # Código generado (compilado proto)
│   ├── sitre_pb2.py
│   └── sitre_pb2_grpc.py
├── resultados/                           # Resultados persistidos (JSON)
└── [otros archivos de configuración]

═══════════════════════════════════════════════════════════════════════════════

FLUJO DE DATOS

1. SERVIDOR (server/main.py)
   ┌─────────────────────────────────────────────────────────┐
   │  main()  Punto de entrada                               │
   └──────────────┬──────────────────────────────────────────┘
                  │
                  ├─→ ModelLoader.load_all()
                  │   └─→ Carga Whisper (asr_model.py)
                  │   └─→ Carga mT5 (summarization_model.py)
                  │
                  ├─→ ResultsStorage() Almacenamiento
                  │
                  └─→ SitreServicer() Servicer gRPC
                      ├─→ TranscriptionService (depende de WhisperASRModel)
                      ├─→ SummarizationService (depende de MT5SummarizationModel)
                      └─→ ResultsStorage (persistencia)

2. CLIENTE (client/app.py)
   ┌──────────────────────────────────┐
   │  Streamlit UI                    │
   └──────────┬───────────────────────┘
              │
              └─→ SitreClient (src/grpc_client.py)
                  ├─→ procesar_audio()
                  ├─→ transcribir()
                  └─→ resumir()

═══════════════════════════════════════════════════════════════════════════════

CAPAS Y RESPONSABILIDADES

┌─────────────────────────────────────────────────────────────────┐
│  CAPA DE PRESENTACIÓN                                           │
│  ├─ client/app.py (Streamlit UI)                               │
│  └─ Este nivel NO contiene lógica de negocio                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  CAPA DE CLIENTE (gRPC)                                         │
│  └─ client/src/grpc_client.py (Comunicación RPC)               │
│     Responsabilidad: Enviar requests y recibir responses        │
└─────────────────────────────────────────────────────────────────┘
                              ↓ (gRPC)
┌─────────────────────────────────────────────────────────────────┐
│  CAPA DE SERVIDOR (gRPC)                                        │
│  └─ src/grpc_servicer.py (SitreServicer)                       │
│     Responsabilidad: Orquestar servicios                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  CAPA DE SERVICIOS (Lógica)                                     │
│  ├─ TranscriptionService → procesa audio                        │
│  ├─ SummarizationService → genera resúmenes                     │
│  └─ Responsabilidad: Lógica de negocio                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  CAPA DE MODELOS (ML)                                           │
│  ├─ WhisperASRModel (Transcripción)                             │
│  ├─ MT5SummarizationModel (Resumen)                             │
│  └─ ModelLoader (Orquestación)                                  │
│     Responsabilidad: Cargar y llamar modelos ML                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  CAPA DE PERSISTENCIA (Storage)                                 │
│  └─ ResultsStorage → Guardado en JSON                           │
│     Responsabilidad: Guardar/recuperar datos                    │
└─────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════

PATRONES DE DISEÑO IMPLEMENTADOS

1. INYECCIÓN DE DEPENDENCIAS
   
   ✗ MAL (Alto acoplamiento):
   class SitreServicer:
       def __init__(self):
           self.asr_model = WhisperASRModel.load()  # Acoplado a carga
           self.summ_model = MT5SummarizationModel.load()

   ✓ BIEN (Bajo acoplamiento):
   class SitreServicer:
       def __init__(self, model_loader, storage):  # Inyectadas
           self.transcription_svc = TranscriptionService(
               model_loader.get_asr_model()
           )

2. SEPARACIÓN DE RESPONSABILIDADES

   ML → Service → gRPC → Client → UI
   
   - ML: Solo cargar y ejecutar modelos
   - Service: Lógica de negocio (manejo de archivos, timeouts, etc)
   - gRPC: Protocolo de comunicación
   - Client: Consumidor de RPC
   - UI: Presentación

3. FACTORY PATTERN

   ModelLoader.load_all() → Punto único de carga
   Permite cambiar modelos sin afectar el resto

4. DATA OBJECTS (NamedTuple)

   TranscripcionResponse, ResumenResponse, ProcesarResponse
   Tipado fuerte sin acoplamiento a protobuf

═══════════════════════════════════════════════════════════════════════════════

BAJA ACOPLACIÓN: EJEMPLOS

1. Cambiar modelo Whisper
   ✓ Modificar: src/models/asr_model.py
   ✗ No afecta: ServiceRequester, Storage, gRPC Servicer

2. Cambiar formato de almacenamiento (JSON → BDD)
   ✓ Modificar: src/storage/results_storage.py
   ✗ No afecta: Services, Models, Servicer gRPC

3. Cambiar UI (Streamlit → FastAPI)
   ✓ Crear: api/main.py
   ✗ Reutilizar: client/src/grpc_client.py

═══════════════════════════════════════════════════════════════════════════════

ALTA COHESIÓN: EJEMPLOS

1. asr_model.py
   - Toda la lógica de Whisper en un lugar
   - Cargar modelo
   - Ejecutar transcripción
   - Manejo de errores específico de ASR

2. transcription_service.py
   - Toda la lógica de transcripción en un lugar
   - Manejo de archivos temporales
   - Conversión de audio
   - Métricas de rendimiento

3. results_storage.py
   - Toda la lógica de almacenamiento en un lugar
   - Guardar resultados
   - Recuperar resultados
   - Listar resultados

═══════════════════════════════════════════════════════════════════════════════

COMENTARIOS PEP 8

Todos los módulos incluyen:

1. Docstring del módulo (primera línea)
   \"\"\"Descripción breve.
   
   Descripción detallada si es necesario.
   \"\"\"

2. Docstring de clases
   class MiClase:
       \"\"\"Descripción de la clase.
       
       Attributes:
           atributo1: Descripción.
       \"\"\"

3. Docstring de métodos
   def mi_metodo(self, param1):
       \"\"\"Descripción breve.
       
       Args:
           param1: Descripción del parámetro.
       
       Returns:
           Descripción del retorno.
       
       Raises:
           ExcepcionTipo: Cuándo se lanza.
       \"\"\"

═══════════════════════════════════════════════════════════════════════════════

GUÍA RÁPIDA: ¿DÓNDE AGREGAR CÓDIGO NUEVO?

Necesito...                          → Archivo
───────────────────────────────────────────────────────────────────
Agregar nuevo comando gRPC           → Modify: proto/sitre.proto
                                        Add method to: src/grpc_servicer.py

Cambiar parámetros de Whisper        → Modify: src/models/asr_model.py

Agregar preprocesamiento de audio    → Modify: src/services/transcription_service.py

Cambiar formato de salida            → Modify: src/storage/results_storage.py
(JSON → CSV, BDD, etc)

Agregar nuevo frontend               → Create: nueva_ui/app.py
                                        Use: client/src/grpc_client.py (reutilizable)

Agregar caché                        → Modify: src/models/model_loader.py
                                        o: src/grpc_servicer.py

═══════════════════════════════════════════════════════════════════════════════
"""  # noqa: E501

# Este archivo es solo documentación, no código ejecutable.

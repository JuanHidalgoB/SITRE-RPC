"""
SITRE-RPC — Cliente Streamlit
"""

import sys
import time
from pathlib import Path

import grpc
import streamlit as st

# Agregar generated al path para importar módulos proto
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_GENERATED_PATH = str(_PROJECT_ROOT / "generated")
if _GENERATED_PATH not in sys.path:
    sys.path.insert(0, _GENERATED_PATH)

try:
    import sitre_pb2
    import sitre_pb2_grpc
except ImportError as e:
    raise ImportError(
        f"No se pudo importar módulos proto. ¿Ejecutaste 'make setup'?\n"
        f"Buscando en: {_GENERATED_PATH}\n"
        f"Error: {e}"
    ) from e

SERVER_ADDR = "localhost:50051"

st.set_page_config(page_title="SITRE-RPC", page_icon="🎙️", layout="centered")

st.markdown("""
<style>
    .title { font-size:2.2rem; font-weight:800; letter-spacing:-1px; }
    .sub   { color:#6b7280; font-family:monospace; font-size:.85rem; margin-bottom:1.5rem; }
    .badge {
        display:inline-block; background:#f3f4f6; border:1px solid #e5e7eb;
        border-radius:4px; padding:2px 10px; font-size:.75rem;
        font-family:monospace; color:#6366f1; margin-right:6px;
    }
    .result {
        background:#1a1a1a; color:#e0e0e0; border-left:3px solid #6366f1;
        border-radius:0 8px 8px 0; padding:1rem 1.2rem;
        font-size:.95rem; line-height:1.7; 
        font-family: 'Courier New', monospace; word-wrap: break-word;
    }
</style>
""", unsafe_allow_html=True)

# ─── Session state initialization ─────────────────────────────────────────────
if "pipeline_result" not in st.session_state:
    st.session_state.pipeline_result = None
if "resumen_result" not in st.session_state:
    st.session_state.resumen_result = None
if "audio_file_name" not in st.session_state:
    st.session_state.audio_file_name = None


@st.cache_resource
def get_stub():
    MB = 1024 * 1024
    options = [
        ("grpc.max_receive_message_length", 100 * MB),
        ("grpc.max_send_message_length",    100 * MB),
    ]
    channel = grpc.insecure_channel(SERVER_ADDR, options=options)
    return sitre_pb2_grpc.SitreServiceStub(channel)


# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown('<div class="title">SITRE-RPC</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub">// Transcripción y Resumen Ejecutivo · gRPC</div>',
    unsafe_allow_html=True,
)

modo = st.radio(
    "Modo",
    ["🎙️ Pipeline completo  (Audio → Transcripción → Resumen)",
     "📝 Solo resumen  (texto directo → Resumen)"],
    horizontal=True,
    label_visibility="collapsed",
)
st.divider()

# ─── Pipeline completo ────────────────────────────────────────────────────────
if "Pipeline" in modo:
    st.markdown(
        '<span class="badge">openai/whisper-tiny</span>'
        '<span class="badge">ELiRF/mt5-base-dacsa-es</span>',
        unsafe_allow_html=True,
    )
    
    # Mostrar resultado si existe
    if st.session_state.pipeline_result:
        resp = st.session_state.pipeline_result
        total = resp.get("total", 0)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("⏱ ASR",    f"{resp['elapsed_asr']}s")
        c2.metric("⏱ Resumen", f"{resp['elapsed_sum']}s")
        c3.metric("⏱ Total",   f"{total}s")
        st.divider()

        st.subheader("📝 Transcripción")
        st.markdown(f'<div class="result">{resp["transcripcion"]}</div>', unsafe_allow_html=True)
        st.download_button("⬇ Descargar transcripción", resp["transcripcion"], "transcripcion.txt")

        st.divider()
        st.subheader("💡 Resumen ejecutivo")
        st.markdown(f'<div class="result">{resp["resumen"]}</div>', unsafe_allow_html=True)
        st.download_button("⬇ Descargar resumen", resp["resumen"], "resumen.txt")
        
        st.divider()
        if st.button("🔄 Procesar otro audio", type="secondary", use_container_width=True):
            st.session_state.pipeline_result = None
            st.rerun()
    else:
        # Formulario para enviar
        audio_file = st.file_uploader(
            "Archivo de audio", type=["mp3", "wav", "m4a", "ogg", "flac"]
        )
        if audio_file:
            st.audio(audio_file)
            if st.button("▶ Procesar", type="primary", use_container_width=True):
                try:
                    stub   = get_stub()
                    t0     = time.time()
                    with st.spinner("Procesando en el servidor gRPC..."):
                        resp = stub.Procesar(
                            sitre_pb2.AudioRequest(
                                audio=audio_file.read(),
                                formato=audio_file.name.rsplit(".", 1)[-1].lower(),
                                idioma="spanish",
                            ),
                            timeout=300,
                        )
                    total = round(time.time() - t0, 2)

                    if resp.error:
                        st.error(f"❌ {resp.error}")
                    else:
                        # Guardar resultado en session_state
                        st.session_state.pipeline_result = {
                            "transcripcion": resp.transcripcion,
                            "resumen": resp.resumen,
                            "elapsed_asr": resp.elapsed_asr,
                            "elapsed_sum": resp.elapsed_sum,
                            "total": total,
                        }
                        st.rerun()

                except grpc.RpcError as e:
                    st.error(f"❌ No se pudo conectar al servidor ({SERVER_ADDR})\n\n"
                             f"`{e.code()}: {e.details()}`\n\n¿Está corriendo `make server`?")

# ─── Solo resumen ─────────────────────────────────────────────────────────────
else:
    st.markdown('<span class="badge">ELiRF/mt5-base-dacsa-es</span>', unsafe_allow_html=True)
    
    # Mostrar resultado si existe
    if st.session_state.resumen_result:
        resp = st.session_state.resumen_result
        
        st.metric("⏱ Tiempo", f"{resp['elapsed_s']}s")
        st.divider()
        st.subheader("💡 Resumen ejecutivo")
        st.markdown(f'<div class="result">{resp["resumen"]}</div>', unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("⬇ Descargar resumen", resp["resumen"], "resumen.txt", use_container_width=True)
        with c2:
            if st.button("🔄 Generar nuevo resumen", type="secondary", use_container_width=True):
                st.session_state.resumen_result = None
                st.rerun()
    else:
        # Formulario para enviar
        texto = st.text_area("Texto en español", height=220,
                             placeholder="Pega aquí el texto que quieres resumir...")
        if st.button("▶ Resumir", type="primary", use_container_width=True):
            if not texto.strip():
                st.warning("Ingresa algún texto primero.")
            else:
                try:
                    stub = get_stub()
                    with st.spinner("Generando resumen..."):
                        resp = stub.Resumir(
                            sitre_pb2.TextoRequest(texto=texto.strip()), timeout=120
                        )
                    if resp.error:
                        st.error(f"❌ {resp.error}")
                    else:
                        # Guardar resultado en session_state
                        st.session_state.resumen_result = {
                            "resumen": resp.resumen,
                            "elapsed_s": resp.elapsed_s,
                        }
                        st.rerun()
                except grpc.RpcError as e:
                    st.error(f"❌ No se pudo conectar al servidor ({SERVER_ADDR})\n\n"
                             f"`{e.code()}: {e.details()}`\n\n¿Está corriendo `make server`?")

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📡 Conexión")
    st.code(SERVER_ADDR)
    st.markdown("### 🤖 Modelos")
    st.markdown("""
**ASR** · `openai/whisper-tiny`
Encoder-Decoder · 39M params

**Resumen** · `ELiRF/mt5-base-dacsa-es`
mT5-base fine-tuned en DACSA · ~580M params
    """)
    st.markdown("### ℹ️ Arquitectura")
    st.code("""Streamlit (cliente)
      ↕  gRPC / HTTP2
  Python Server
  ├─ Whisper-tiny
  └─ mT5-dacsa-es""")

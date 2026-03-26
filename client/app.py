"""SITRE-RPC — Cliente Streamlit.

Aplicación web interactiva para transcribir audio y generar resúmenes
mediante el servidor SITRE-RPC.
"""

import os
import sys
import time
from pathlib import Path

import streamlit as st

# Agregar client/src al path para importar módulos propios
_PROJECT_ROOT = Path(__file__).resolve().parent
_CLIENT_SRC_PATH = str(_PROJECT_ROOT / "src")
if _CLIENT_SRC_PATH not in sys.path:
    sys.path.insert(0, _CLIENT_SRC_PATH)

from grpc_client import SitreClient

# ─── Configuración ────────────────────────────────────────────────────────────

SERVER_ADDR = os.getenv("SITRE_SERVER_ADDR", "localhost:50051")

st.set_page_config(page_title="SITRE-RPC", page_icon="🎙️", layout="centered")

st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)

# ─── Session state initialization ─────────────────────────────────────────────
if "pipeline_result" not in st.session_state:
    st.session_state.pipeline_result = None
if "resumen_result" not in st.session_state:
    st.session_state.resumen_result = None


@st.cache_resource
def get_client():
    """Obtiene el cliente gRPC (cacheado).

    Returns:
        Instancia de SitreClient conectada al servidor.
    """
    try:
        return SitreClient(SERVER_ADDR)
    except Exception as e:
        st.error(f"No se puede conectar a {SERVER_ADDR}: {e}")
        return None


# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown('<div class="title">SITRE-RPC</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub">// Transcripción y Resumen Ejecutivo · gRPC</div>',
    unsafe_allow_html=True,
)

modo = st.radio(
    "Modo",
    [
        "🎙️ Pipeline completo  (Audio → Transcripción → Resumen)",
        "📝 Solo resumen  (texto directo → Resumen)",
    ],
    horizontal=True,
    label_visibility="collapsed",
)
st.divider()

# ─── Pipeline completo ────────────────────────────────────────────────────────
if "Pipeline" in modo:
    st.markdown(
        '<span class="badge">openai/whisper-small</span>'
        '<span class="badge">ELiRF/mt5-base-dacsa-es</span>',
        unsafe_allow_html=True,
    )

    # Mostrar resultado si existe
    if st.session_state.pipeline_result:
        result = st.session_state.pipeline_result

        c1, c2, c3 = st.columns(3)
        c1.metric("⏱ ASR", f"{result['elapsed_asr']}s")
        c2.metric("⏱ Resumen", f"{result['elapsed_sum']}s")
        c3.metric("⏱ Total", f"{result['total']}s")
        st.divider()

        st.subheader("📝 Transcripción")
        st.markdown(
            f'<div class="result">{result["transcripcion"]}</div>',
            unsafe_allow_html=True,
        )
        st.download_button(
            "⬇ Descargar transcripción",
            result["transcripcion"],
            "transcripcion.txt",
        )

        st.divider()
        st.subheader("💡 Resumen ejecutivo")
        st.markdown(
            f'<div class="result">{result["resumen"]}</div>',
            unsafe_allow_html=True,
        )
        st.download_button("⬇ Descargar resumen", result["resumen"], "resumen.txt")

        st.divider()
        if st.button("🔄 Procesar otro audio", type="secondary", use_container_width=True):
            st.session_state.pipeline_result = None
            st.rerun()
    else:
        # Formulario para enviar
        audio_file = st.file_uploader("Archivo de audio", type=["mp3", "wav", "m4a", "ogg", "flac"])
        if audio_file:
            st.audio(audio_file)
            if st.button("▶ Procesar", type="primary", use_container_width=True):
                try:
                    client = get_client()
                    if not client:
                        st.error(f"❌ No se puede conectar al servidor ({SERVER_ADDR})")
                        st.stop()

                    t0 = time.time()

                    # Contenedor para la barra de progreso
                    progress_container = st.container()
                    status_text = progress_container.empty()
                    progress_bar = progress_container.progress(0)

                    status_text.info("⏳ **Conectando al servidor...**")
                    progress_bar.progress(5)
                    time.sleep(0.5)

                    status_text.info("🎙️ **Transcribiendo audio...**")
                    progress_bar.progress(25)

                    # Procesamiento en el servidor
                    fmt = audio_file.name.rsplit(".", 1)[-1].lower()
                    resp = client.procesar_audio(
                        audio_bytes=audio_file.read(),
                        formato=fmt,
                        idioma="spanish",
                    )

                    progress_bar.progress(75)
                    status_text.info("📝 **Generando resumen...**")
                    time.sleep(0.5)

                    progress_bar.progress(90)
                    status_text.info("💾 **Finalizando...**")
                    time.sleep(0.5)

                    total = round(time.time() - t0, 2)

                    if resp.error:
                        progress_container.empty()
                        st.error(f"❌ {resp.error}")
                    else:
                        progress_bar.progress(100)
                        progress_container.empty()

                        # Guardar resultado en session_state
                        st.session_state.pipeline_result = {
                            "transcripcion": resp.transcripcion,
                            "resumen": resp.resumen,
                            "elapsed_asr": resp.elapsed_asr,
                            "elapsed_sum": resp.elapsed_sum,
                            "total": total,
                        }
                        st.success("✅ Procesamiento completado")
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Error: {e}")

# ─── Solo resumen ─────────────────────────────────────────────────────────────
else:
    st.markdown(
        '<span class="badge">ELiRF/mt5-base-dacsa-es</span>',
        unsafe_allow_html=True,
    )

    # Mostrar resultado si existe
    if st.session_state.resumen_result:
        result = st.session_state.resumen_result

        st.metric("⏱ Tiempo", f"{result['elapsed_s']}s")
        st.divider()
        st.subheader("💡 Resumen ejecutivo")
        st.markdown(
            f'<div class="result">{result["resumen"]}</div>',
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "⬇ Descargar resumen",
                result["resumen"],
                "resumen.txt",
                use_container_width=True,
            )
        with c2:
            if st.button(
                "🔄 Generar nuevo resumen",
                type="secondary",
                use_container_width=True,
            ):
                st.session_state.resumen_result = None
                st.rerun()
    else:
        # Formulario para enviar
        texto = st.text_area(
            "Texto en español",
            height=220,
            placeholder="Pega aquí el texto que quieres resumir...",
        )
        if st.button("▶ Resumir", type="primary", use_container_width=True):
            if not texto.strip():
                st.warning("Ingresa algún texto primero.")
            else:
                try:
                    client = get_client()
                    if not client:
                        st.error(f"❌ No se puede conectar al servidor ({SERVER_ADDR})")
                        st.stop()

                    with st.spinner("Generando resumen..."):
                        resp = client.resumir(texto.strip())

                    if resp.error:
                        st.error(f"❌ {resp.error}")
                    else:
                        # Guardar resultado en session_state
                        st.session_state.resumen_result = {
                            "resumen": resp.resumen,
                            "elapsed_s": resp.elapsed_s,
                        }
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Error: {e}")

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📡 Conexión")
    st.code(SERVER_ADDR)
    st.markdown("### 🤖 Modelos")
    st.markdown(
        """
**ASR** · `openai/whisper-small`
Encoder-Decoder · 244M params

**Resumen** · `ELiRF/mt5-base-dacsa-es`
mT5-base fine-tuned en DACSA · ~580M params
    """
    )
    st.markdown("### ℹ️ Arquitectura")
    st.code(
        """Streamlit (cliente)
      ↕  gRPC / HTTP2
  Python Server
  ├─ Whisper-small
  └─ mT5-dacsa-es"""
    )

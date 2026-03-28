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

st.set_page_config(page_title="SITRE", page_icon="🎙️", layout="centered")

st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ── Base ── */
    .stApp {
        background-color: #131722;
        font-family: 'Inter', sans-serif;
    }
    html, body, [class*="css"] {
        color: #CBD5E0;
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3, h4 { color: #ffffff !important; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background-color: #1B1F2A;
        border-right: 1px solid #2E3344;
    }
    [data-testid="stSidebar"] * { color: #A0AEC0; }
    [data-testid="stSidebar"] h3 { color: #ffffff !important; }
    [data-testid="stSidebar"] code {
        background: #131722 !important;
        color: #FFD86F !important;
        border: 1px solid #2E3344 !important;
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* ── Hero header ── */
    .hero {
        text-align: center;
        padding: 2.5rem 0 1rem 0;
    }
    .hero-eyebrow {
        font-family: 'JetBrains Mono', monospace;
        font-size: .72rem;
        letter-spacing: .18em;
        text-transform: uppercase;
        color: #FC9882;
        margin-bottom: .6rem;
    }
    .hero-title {
        font-size: 3.4rem;
        font-weight: 800;
        letter-spacing: -2px;
        line-height: 1;
        background: linear-gradient(100deg, #FFD86F 0%, #FC9882 60%, #e879f9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: .5rem;
    }
    .hero-sub {
        font-family: 'JetBrains Mono', monospace;
        font-size: .82rem;
        color: #A0AEC0;
        margin-bottom: 1.8rem;
    }

    /* ── Mode selector card ── */
    .mode-card {
        display: flex;
        gap: 12px;
        margin-bottom: 1.5rem;
    }
    .mode-btn {
        flex: 1;
        background: #1B1F2A;
        border: 1px solid #2E3344;
        border-radius: 10px;
        padding: 1rem;
        cursor: pointer;
        transition: all .2s;
        text-align: center;
    }
    .mode-btn:hover { border-color: #FFD86F; }
    .mode-btn.active {
        border-color: #FFD86F;
        background: #232734;
        box-shadow: 0 0 20px rgba(255,216,111,.12);
    }

    /* ── Section card ── */
    .section-card {
        background: #1B1F2A;
        border: 1px solid #2E3344;
        border-radius: 12px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1rem;
    }
    .section-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: .7rem;
        letter-spacing: .15em;
        text-transform: uppercase;
        color: #A0AEC0;
        margin-bottom: .5rem;
    }

    /* ── Badges ── */
    .badge {
        display: inline-block;
        background: #131722;
        border: 1px solid #2E3344;
        border-radius: 6px;
        padding: 3px 12px;
        font-size: .72rem;
        font-family: 'JetBrains Mono', monospace;
        color: #FFD86F;
        margin-right: 6px;
        margin-bottom: 6px;
    }
    .badge-purple { color: #c084fc; border-color: #3d2a4e; background: #1e1628; }
    .badge-teal   { color: #5eead4; border-color: #1a3a37; background: #131f1e; }

    /* ── Resultado ── */
    .result-block {
        background: #232734;
        border: 1px solid #2E3344;
        border-radius: 10px;
        padding: 1.2rem 1.4rem;
        font-size: .93rem;
        line-height: 1.75;
        font-family: 'Inter', sans-serif;
        color: #CBD5E0;
        word-wrap: break-word;
        white-space: pre-wrap;
    }
    .result-accent {
        border-left: 3px solid #FFD86F;
        border-radius: 0 10px 10px 0;
    }
    .result-accent-purple {
        border-left: 3px solid #c084fc;
        border-radius: 0 10px 10px 0;
    }
    .result-header {
        display: flex;
        align-items: center;
        gap: .5rem;
        margin-bottom: .75rem;
        font-weight: 700;
        font-size: .95rem;
        color: #ffffff;
    }
    .result-header-icon {
        font-size: 1.1rem;
    }

    /* ── Métricas custom ── */
    .metrics-row {
        display: flex;
        gap: 12px;
        margin-bottom: 1.2rem;
    }
    .metric-card {
        flex: 1;
        background: #232734;
        border: 1px solid #2E3344;
        border-radius: 10px;
        padding: .85rem 1rem;
        text-align: center;
    }
    .metric-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: .65rem;
        letter-spacing: .12em;
        text-transform: uppercase;
        color: #A0AEC0;
        margin-bottom: .3rem;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #FFD86F, #FC9882);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1.1;
    }

    /* ── Status processing ── */
    .status-processing {
        background: #1a1f2e;
        border: 1px solid #2E3344;
        border-left: 3px solid #FFD86F;
        border-radius: 0 10px 10px 0;
        padding: .9rem 1.2rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: .82rem;
        color: #FFD86F;
        margin-bottom: .75rem;
        animation: pulse-border 2s infinite;
    }
    @keyframes pulse-border {
        0%, 100% { border-left-color: #FFD86F; }
        50%       { border-left-color: #FC9882; }
    }

    /* ── Botones ── */
    [data-testid="stButton"] button[kind="primary"] {
        background: linear-gradient(90deg, #FFD86F, #FC9882) !important;
        color: #131722 !important;
        font-weight: 700 !important;
        font-family: 'Inter', sans-serif !important;
        border: none !important;
        border-radius: 8px !important;
        transition: all .2s !important;
    }
    [data-testid="stButton"] button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 24px rgba(255,216,111,.3) !important;
    }
    [data-testid="stButton"] button[kind="secondary"] {
        background: #1B1F2A !important;
        color: #FFD86F !important;
        border: 1px solid #2E3344 !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
    }
    [data-testid="stButton"] button[kind="secondary"]:hover {
        border-color: #FFD86F !important;
        background: #232734 !important;
    }
    [data-testid="stDownloadButton"] button {
        background: #1B1F2A !important;
        color: #A0AEC0 !important;
        border: 1px solid #2E3344 !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* ── Inputs ── */
    [data-testid="stTextArea"] textarea {
        background-color: #1B1F2A !important;
        border: 1px solid #2E3344 !important;
        border-radius: 8px !important;
        color: #CBD5E0 !important;
        font-family: 'Inter', sans-serif !important;
    }
    [data-testid="stTextArea"] textarea:focus {
        border-color: #FFD86F !important;
        box-shadow: 0 0 0 2px rgba(255,216,111,.15) !important;
    }
    [data-testid="stFileUploader"] {
        background: #1B1F2A !important;
        border: 1px dashed #2E3344 !important;
        border-radius: 10px !important;
    }

    /* ── Radio ── */
    [data-testid="stRadio"] > div { gap: 12px !important; }
    [data-testid="stRadio"] label {
        background: #1B1F2A;
        border: 1px solid #2E3344;
        border-radius: 8px;
        padding: .6rem 1.1rem !important;
        color: #A0AEC0 !important;
        transition: all .2s;
    }
    [data-testid="stRadio"] label:hover { border-color: #FFD86F; }
    [data-testid="stRadio"] label:has(input:checked) {
        border-color: #FFD86F !important;
        color: #FFD86F !important;
        background: #232734 !important;
    }

    /* ── Divisor ── */
    hr { border-color: #2E3344 !important; margin: 1.5rem 0 !important; }

    /* ── Alertas ── */
    [data-testid="stAlert"] {
        background-color: #1B1F2A !important;
        border: 1px solid #2E3344 !important;
        border-radius: 8px !important;
        color: #CBD5E0 !important;
    }

    /* ── Audio player ── */
    audio { width: 100%; border-radius: 8px; margin: .5rem 0; }

    /* ── Progress bar ── */
    [data-testid="stProgress"] > div > div {
        background: linear-gradient(90deg, #FFD86F, #FC9882) !important;
        border-radius: 99px !important;
    }
    [data-testid="stProgress"] > div {
        background: #232734 !important;
        border-radius: 99px !important;
        height: 6px !important;
    }

    /* ── Ocultar header Streamlit ── */
    #MainMenu, header, footer { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }
</style>
""",
    unsafe_allow_html=True,
)

# ─── Session state initialization ─────────────────────────────────────────────
if "pipeline_result" not in st.session_state:
    st.session_state.pipeline_result = None
if "resumen_result" not in st.session_state:
    st.session_state.resumen_result = None
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False


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


# ─── Hero Header ──────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="hero">
    <div class="hero-eyebrow">Sistema distribuido · gRPC · IA</div>
    <div class="hero-title">SITRE</div>
    <div class="hero-sub">Transcripción automática &amp; Resumen ejecutivo en español</div>
</div>
""",
    unsafe_allow_html=True,
)

modo = st.radio(
    "Modo",
    [
        "🎙️  Pipeline completo — Audio → Transcripción → Resumen",
        "📝  Solo resumen — Texto directo → Resumen",
    ],
    horizontal=True,
    label_visibility="collapsed",
)
st.divider()

# ─── Pipeline completo ────────────────────────────────────────────────────────
if "Pipeline" in modo:
    st.markdown(
        '<span class="badge">openai/whisper-small</span>'
        '<span class="badge badge-purple">ELiRF/mt5-base-dacsa-es</span>'
        '<span class="badge badge-teal">gRPC / HTTP2</span>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state.pipeline_result:
        result = st.session_state.pipeline_result

        # Métricas
        st.markdown(
            f"""
<div class="metrics-row">
    <div class="metric-card">
        <div class="metric-label">ASR · Whisper</div>
        <div class="metric-value">{result['elapsed_asr']}s</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Resumen · mT5</div>
        <div class="metric-value">{result['elapsed_sum']}s</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Total pipeline</div>
        <div class="metric-value">{result['total']}s</div>
    </div>
</div>
""",
            unsafe_allow_html=True,
        )

        # Transcripción
        st.markdown(
            f"""
<div class="result-header"><span class="result-header-icon">📝</span> Transcripción</div>
<div class="result-block result-accent">{result["transcripcion"]}</div>
""",
            unsafe_allow_html=True,
        )
        st.download_button(
            "⬇  Descargar transcripción",
            result["transcripcion"],
            "transcripcion.txt",
            use_container_width=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Resumen
        st.markdown(
            f"""
<div class="result-header"><span class="result-header-icon">💡</span> Resumen ejecutivo</div>
<div class="result-block result-accent-purple">{result["resumen"]}</div>
""",
            unsafe_allow_html=True,
        )
        st.download_button(
            "⬇  Descargar resumen",
            result["resumen"],
            "resumen.txt",
            use_container_width=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄  Procesar otro audio", type="secondary", use_container_width=True):
            st.session_state.pipeline_result = None
            st.rerun()

    else:
        audio_file = st.file_uploader(
            "Arrastra tu archivo de audio aquí",
            type=["mp3", "wav", "m4a", "ogg", "flac"],
            label_visibility="visible",
        )
        if audio_file:
            audio_bytes = audio_file.read()
            st.audio(audio_bytes)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(
                "▶  Procesar audio",
                type="primary",
                use_container_width=True,
                disabled=st.session_state.is_processing,
            ):
                try:
                    st.session_state.is_processing = True
                    client = get_client()
                    if not client:
                        st.error(f"❌ No se puede conectar al servidor ({SERVER_ADDR})")
                        st.session_state.is_processing = False
                        st.stop()

                    t0 = time.time()
                    status = st.empty()
                    bar = st.progress(0)

                    status.markdown(
                        '<div class="status-processing">⚡ Conectando al servidor...</div>',
                        unsafe_allow_html=True,
                    )
                    bar.progress(5)
                    time.sleep(0.4)

                    status.markdown(
                        '<div class="status-processing">🎙️ Transcribiendo con Whisper — esto puede tardar varios minutos...</div>',
                        unsafe_allow_html=True,
                    )
                    bar.progress(20)

                    fmt = audio_file.name.rsplit(".", 1)[-1].lower()
                    resp = client.procesar_audio(
                        audio_bytes=audio_bytes,
                        formato=fmt,
                        idioma="spanish",
                    )

                    status.markdown(
                        '<div class="status-processing">💡 Generando resumen ejecutivo...</div>',
                        unsafe_allow_html=True,
                    )
                    bar.progress(85)
                    time.sleep(0.4)

                    bar.progress(100)
                    total = round(time.time() - t0, 2)

                    if resp.error:
                        status.empty()
                        bar.empty()
                        st.error(f"❌ {resp.error}")
                    else:
                        status.empty()
                        bar.empty()
                        st.session_state.pipeline_result = {
                            "transcripcion": resp.transcripcion,
                            "resumen": resp.resumen,
                            "elapsed_asr": resp.elapsed_asr,
                            "elapsed_sum": resp.elapsed_sum,
                            "total": total,
                        }
                        st.session_state.is_processing = False
                        st.rerun()

                except Exception as e:
                    st.session_state.is_processing = False
                    st.error(f"❌ Error: {e}")

# ─── Solo resumen ─────────────────────────────────────────────────────────────
else:
    st.markdown(
        '<span class="badge badge-purple">ELiRF/mt5-base-dacsa-es</span>'
        '<span class="badge badge-teal">gRPC / HTTP2</span>',
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    if st.session_state.resumen_result:
        result = st.session_state.resumen_result

        st.markdown(
            f"""
<div class="metrics-row">
    <div class="metric-card" style="max-width:200px;">
        <div class="metric-label">Tiempo · mT5</div>
        <div class="metric-value">{result['elapsed_s']}s</div>
    </div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
<div class="result-header"><span class="result-header-icon">💡</span> Resumen ejecutivo</div>
<div class="result-block result-accent-purple">{result["resumen"]}</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "⬇  Descargar resumen",
                result["resumen"],
                "resumen.txt",
                use_container_width=True,
            )
        with c2:
            if st.button("🔄  Nuevo resumen", type="secondary", use_container_width=True):
                st.session_state.resumen_result = None
                st.rerun()

    else:
        texto = st.text_area(
            "Texto en español",
            height=220,
            placeholder="Pega aquí el texto que quieres resumir...",
        )
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("▶  Generar resumen", type="primary", use_container_width=True):
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
    st.code(SERVER_ADDR, language=None)

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
  └─ mT5-dacsa-es""",
        language=None,
    )

"""
SITRE-RPC — Servidor gRPC
Optimizado para CPU. Usa el mecanismo nativo de Whisper para audio largo.
"""

import sys
import time
import tempfile
import logging
from concurrent import futures
from pathlib import Path

# Agregar generated al path para importar módulos proto
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_GENERATED_PATH = str(_PROJECT_ROOT / "generated")
if _GENERATED_PATH not in sys.path:
    sys.path.insert(0, _GENERATED_PATH)

import grpc
import torch
import numpy as np
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoModelForSpeechSeq2Seq,
    AutoProcessor,
    AutoTokenizer,
    WhisperProcessor,
)

try:
    import sitre_pb2
    import sitre_pb2_grpc
except ImportError as e:
    raise ImportError(
        f"No se pudo importar módulos proto. ¿Ejecutaste 'make setup'?\n"
        f"Buscando en: {_GENERATED_PATH}\n"
        f"Error: {e}"
    ) from e

HOST   = "localhost"
PORT   = 50051
DEVICE = "cpu"
DTYPE  = torch.float32

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SERVER] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ─── Carga de modelos ─────────────────────────────────────────────────────────

def cargar_modelos():
    log.info(f"Dispositivo: CPU | Threads: {torch.get_num_threads()}")

    # ── Whisper ───────────────────────────────────────────────────────────────
    # Usamos AutoModelForSpeechSeq2Seq + generate() directamente
    # para aprovechar el chunking nativo de Whisper (paper §3.8)
    log.info("[1/2] Cargando Whisper-tiny...")
    t0 = time.time()
    whisper_processor = WhisperProcessor.from_pretrained("openai/whisper-tiny")
    whisper_model = AutoModelForSpeechSeq2Seq.from_pretrained(
        "openai/whisper-tiny",
        torch_dtype=DTYPE,
        low_cpu_mem_usage=True,
    )
    log.info(f"Whisper listo en {time.time()-t0:.1f}s")

    # ── mT5 ───────────────────────────────────────────────────────────────────
    # Los pesos encoder/decoder.embed_tokens se comparten con shared.weight
    # en mT5 — hay que copiarlos explícitamente después de cargar
    log.info("[2/2] Cargando mT5-base-dacsa-es...")
    t0 = time.time()
    sum_tokenizer = AutoTokenizer.from_pretrained("ELiRF/mt5-base-dacsa-es")
    sum_model = AutoModelForSeq2SeqLM.from_pretrained(
        "ELiRF/mt5-base-dacsa-es",
        torch_dtype=DTYPE,
        low_cpu_mem_usage=True,
    )
    # Corregir los embeddings faltantes — en mT5 comparten pesos con shared
    shared = sum_model.shared.weight.data
    sum_model.encoder.embed_tokens.weight.data.copy_(shared)
    sum_model.decoder.embed_tokens.weight.data.copy_(shared)
    log.info(f"mT5 listo en {time.time()-t0:.1f}s")

    return whisper_processor, whisper_model, sum_tokenizer, sum_model


# ─── Inferencia ASR ───────────────────────────────────────────────────────────

def _transcribir(processor, model, audio_bytes, formato, idioma):
    import librosa  # lazy import — solo cuando se necesita

    ext = f".{formato}" if formato else ".mp3"
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
        f.write(audio_bytes)
        tmp = f.name

    t0 = time.time()

    # Cargar y resamplear a 16kHz (requerido por Whisper)
    audio, sr = librosa.load(tmp, sr=16000, mono=True)
    Path(tmp).unlink(missing_ok=True)

    # Procesar con el mecanismo nativo de long-form de Whisper
    inputs = processor(
        audio,
        sampling_rate=16000,
        return_tensors="pt",
    )
    input_features = inputs.input_features

    forced_ids = processor.get_decoder_prompt_ids(
        language=idioma or "spanish",
        task="transcribe",
    )

    with torch.no_grad():
        predicted_ids = model.generate(
            input_features,
            forced_decoder_ids=forced_ids,
            # Chunking nativo para audio largo
            condition_on_prev_tokens=True,
            temperature=0.0,
            compression_ratio_threshold=2.4,
            logprob_threshold=-1.0,
            no_speech_threshold=0.6,
        )

    transcripcion = processor.batch_decode(predicted_ids, skip_special_tokens=True)
    elapsed = round(time.time() - t0, 2)
    return " ".join(transcripcion).strip(), elapsed


# ─── Inferencia Resumen ───────────────────────────────────────────────────────

def _resumir(tokenizer, model, texto):
    inputs = tokenizer(
        texto,
        return_tensors="pt",
        max_length=512,
        truncation=True,
    )
    t0 = time.time()
    with torch.no_grad():
        ids = model.generate(
            **inputs,
            max_new_tokens=150,
            min_length=30,
            num_beams=4,
            early_stopping=True,
            no_repeat_ngram_size=3,
        )
    elapsed = round(time.time() - t0, 2)
    return tokenizer.decode(ids[0], skip_special_tokens=True), elapsed


# ─── Servicer gRPC ────────────────────────────────────────────────────────────

class SitreServicer(sitre_pb2_grpc.SitreServiceServicer):

    def __init__(self, whisper_processor, whisper_model, sum_tokenizer, sum_model):
        self.w_processor = whisper_processor
        self.w_model     = whisper_model
        self.s_tokenizer = sum_tokenizer
        self.s_model     = sum_model

    def Transcribir(self, request, context):
        log.info("RPC Transcribir")
        try:
            texto, elapsed = _transcribir(
                self.w_processor, self.w_model,
                request.audio, request.formato, request.idioma,
            )
            log.info(f"Transcripción: {len(texto)} chars en {elapsed}s")
            return sitre_pb2.TranscripcionResponse(transcripcion=texto, elapsed_s=elapsed)
        except Exception as e:
            log.error(f"Error: {e}")
            return sitre_pb2.TranscripcionResponse(error=str(e))

    def Resumir(self, request, context):
        log.info("RPC Resumir")
        try:
            resumen, elapsed = _resumir(self.s_tokenizer, self.s_model, request.texto)
            log.info(f"Resumen: {len(resumen)} chars en {elapsed}s")
            return sitre_pb2.ResumenResponse(resumen=resumen, elapsed_s=elapsed)
        except Exception as e:
            log.error(f"Error: {e}")
            return sitre_pb2.ResumenResponse(error=str(e))

    def Procesar(self, request, context):
        log.info("RPC Procesar — pipeline completo")
        try:
            texto, e_asr = _transcribir(
                self.w_processor, self.w_model,
                request.audio, request.formato, request.idioma,
            )
            resumen, e_sum = _resumir(self.s_tokenizer, self.s_model, texto)
            log.info(f"ASR={e_asr}s | SUM={e_sum}s")
            return sitre_pb2.ProcesarResponse(
                transcripcion=texto, resumen=resumen,
                elapsed_asr=e_asr, elapsed_sum=e_sum,
            )
        except Exception as e:
            log.error(f"Error: {e}")
            return sitre_pb2.ProcesarResponse(error=str(e))


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    w_processor, w_model, s_tokenizer, s_model = cargar_modelos()

    MB = 1024 * 1024
    options = [
        ("grpc.max_receive_message_length", 100 * MB),
        ("grpc.max_send_message_length",    100 * MB),
    ]
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4), options=options)
    sitre_pb2_grpc.add_SitreServiceServicer_to_server(
        SitreServicer(w_processor, w_model, s_tokenizer, s_model), server
    )
    server.add_insecure_port(f"{HOST}:{PORT}")
    server.start()
    log.info(f"Escuchando en {HOST}:{PORT}")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(grace=5)
        log.info("Servidor detenido.")


if __name__ == "__main__":
    main()
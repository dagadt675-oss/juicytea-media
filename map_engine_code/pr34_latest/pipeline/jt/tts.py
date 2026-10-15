"""Placeholder voice. espeak-ng word events, or an external wav + alignment.

ElevenLabs is not called. Drop a per-line wav and a words JSON in the spec
(`voice.takes`) when a real read exists. `engine: whisper` aligns a wav with
faster-whisper when that package is installed.
"""

from __future__ import annotations

import ctypes
import json
import wave
from pathlib import Path

import numpy as np

from jt.captions import is_keyword, tokenize

_LIB = None
_CB = None
_STATE = {"chunks": [], "words": []}


class _Event(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_int),
        ("unique_identifier", ctypes.c_uint),
        ("text_position", ctypes.c_int),
        ("length", ctypes.c_int),
        ("audio_position", ctypes.c_int),
        ("sample", ctypes.c_int),
        ("user_data", ctypes.c_void_p),
        ("number", ctypes.c_int),
        ("pad", ctypes.c_int),
    ]


def _lib():
    global _LIB, _CB
    if _LIB is not None:
        return _LIB
    lib = ctypes.CDLL("libespeak-ng.so.1")
    lib.espeak_Initialize.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
    lib.espeak_Initialize.restype = ctypes.c_int
    sr = lib.espeak_Initialize(1, 200, None, 0)  # AUDIO_OUTPUT_RETRIEVAL
    if sr <= 0:
        raise RuntimeError("espeak_Initialize failed")
    lib._sr = sr

    CB = ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_short),
        ctypes.c_int,
        ctypes.POINTER(_Event),
    )

    @CB
    def _on_audio(wav, n, events):
        if n > 0:
            _STATE["chunks"].append(np.ctypeslib.as_array(wav, shape=(n,)).copy())
        i = 0
        while i < 400:
            ev = events[i]
            if ev.type == 0:
                break
            if ev.type == 1:
                _STATE["words"].append((ev.text_position, ev.length, ev.audio_position))
            i += 1
        return 0

    lib.espeak_SetSynthCallback.argtypes = [CB]
    lib.espeak_SetSynthCallback(_on_audio)
    lib.espeak_SetVoiceByName.argtypes = [ctypes.c_char_p]
    lib.espeak_SetParameter.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
    lib.espeak_Synth.argtypes = [
        ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint, ctypes.c_int,
        ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_uint), ctypes.c_void_p,
    ]
    lib.espeak_Synth.restype = ctypes.c_int
    lib.espeak_Synchronize.restype = ctypes.c_int
    _CB = _on_audio  # keep alive
    _LIB = lib
    return lib


def speak(text: str, voice: str = "en-us", rate: int = 138) -> tuple[np.ndarray, int, list[dict]]:
    lib = _lib()
    lib.espeak_SetVoiceByName(voice.encode())
    lib.espeak_SetParameter(1, int(rate), 0)  # espeakRATE
    _STATE["chunks"] = []
    _STATE["words"] = []
    raw = text.encode("utf-8")
    uid = ctypes.c_uint(0)
    rc = lib.espeak_Synth(raw, len(raw) + 1, 0, 0, 0, 0, ctypes.byref(uid), None)
    if rc != 0:
        raise RuntimeError(f"espeak_Synth returned {rc}")
    lib.espeak_Synchronize()
    if not _STATE["chunks"]:
        raise RuntimeError("espeak produced no audio")
    audio = np.concatenate(_STATE["chunks"]).astype(np.float32) / 32768.0
    sr = lib._sr
    dur = len(audio) / sr
    events = []
    for pos, length, ms in _STATE["words"]:
        # espeak positions are 1-based into the UTF-8 byte string for ASCII.
        start = max(0, pos - 1)
        piece = raw[start:start + max(0, length)].decode("utf-8", "ignore")
        events.append({"text": piece, "start": ms / 1000.0})
    words = _align_script(text, events, dur)
    return audio, sr, words


def _align_script(text: str, events: list[dict], dur: float) -> list[dict]:
    tokens = tokenize(text)
    if not tokens:
        return []
    if len(events) == len(tokens):
        starts = [e["start"] for e in events] + [dur]
        out = []
        for tok, a, b in zip(tokens, starts, starts[1:]):
            out.append(_word(tok, a, max(b, a + 0.04)))
        return out
    # Character-proportional fallback inside the spoken duration.
    weights = [max(1, sum(c.isalnum() for c in t)) for t in tokens]
    total = sum(weights)
    t = 0.0
    out = []
    for tok, w in zip(tokens, weights):
        span = dur * w / total
        out.append(_word(tok, t, t + max(0.04, span)))
        t += span
    return out


def _word(text: str, start: float, end: float) -> dict:
    return {
        "text": text,
        "start": round(float(start), 4),
        "end": round(float(end), 4),
        "keyword": is_keyword(text),
    }


def load_words_json(path: Path, script: str) -> list[dict]:
    raw = json.loads(Path(path).read_text())
    if "words" in raw:
        out = []
        for w in raw["words"]:
            text = str(w.get("text") or w.get("word") or w.get("w"))
            start = float(w.get("start", w.get("t0")))
            end = float(w.get("end", w.get("t1")))
            out.append(_word(text, start, end))
        return out
    chars = raw.get("characters") or raw.get("alignment", {}).get("characters")
    starts = (raw.get("character_start_times_seconds")
              or raw.get("alignment", {}).get("character_start_times_seconds"))
    ends = (raw.get("character_end_times_seconds")
            or raw.get("alignment", {}).get("character_end_times_seconds"))
    if not chars or not starts:
        raise ValueError(f"unrecognised alignment json: {path}")
    # Group characters into the script's tokens.
    tokens = tokenize(script)
    flat = []
    for ch, a, b in zip(chars, starts, ends):
        flat.append((ch, float(a), float(b)))
    # Rebuild by walking non-space characters.
    out = []
    idx = 0
    for tok in tokens:
        letters = [c for c in tok if not c.isspace()]
        if idx >= len(flat):
            break
        a = flat[idx][1]
        b = flat[idx][2]
        need = len(letters)
        got = 0
        while idx < len(flat) and got < need:
            ch, _, end = flat[idx]
            if ch.isspace():
                idx += 1
                continue
            b = end
            got += 1
            idx += 1
        out.append(_word(tok, a, b))
    return out


def read_wav(path: Path) -> tuple[np.ndarray, int]:
    import soundfile as sf
    audio, sr = sf.read(str(path), dtype="float32", always_2d=False)
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    return audio.astype(np.float32), int(sr)


def write_wav(path: Path, audio: np.ndarray, sr: int) -> None:
    import soundfile as sf
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), np.asarray(audio, np.float32), sr)


def align_whisper(wav_path: Path, script: str, model_name: str = "small.en") -> list[dict]:
    from faster_whisper import WhisperModel
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, _info = model.transcribe(
        str(wav_path),
        word_timestamps=True,
        language="en",
        vad_filter=False,
        initial_prompt=script,
        condition_on_previous_text=False,
    )
    heard = []
    for seg in segments:
        if not seg.words:
            continue
        for w in seg.words:
            heard.append(_word(w.word.strip(), w.start, w.end))
    tokens = tokenize(script)
    if len(heard) == len(tokens):
        out = []
        for tok, h in zip(tokens, heard):
            out.append(_word(tok, h["start"], h["end"]))
        return out
    return heard

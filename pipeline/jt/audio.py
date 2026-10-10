"""Assemble takes, duck procedural SFX, keyword tail gain, 2-pass loudnorm.

No sample libraries. Whoosh / pop / tick / ding / swell are synthesised.
SFX peaks stay at least 12 dB under the voice peak (the gate is 10 dB).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
from scipy.signal import butter, lfilter

from jt.captions import is_keyword
from jt.tts import align_whisper, load_words_json, read_wav, speak, write_wav

SR = 48000


def _resample(audio: np.ndarray, src_sr: int, dst_sr: int = SR) -> np.ndarray:
    if src_sr == dst_sr:
        return audio.astype(np.float32)
    from math import gcd
    from scipy.signal import resample_poly
    g = gcd(src_sr, dst_sr)
    return resample_poly(audio, dst_sr // g, src_sr // g).astype(np.float32)


def _rms(x: np.ndarray) -> float:
    if len(x) == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(x.astype(np.float64)))))


def _match_rms(x: np.ndarray, db: float) -> np.ndarray:
    cur = _rms(x)
    if cur < 1e-8:
        return x
    return x * (10 ** (db / 20.0) / cur)


def _room(n: int, rng: np.random.Generator) -> np.ndarray:
    if n <= 0:
        return np.zeros(0, np.float32)
    noise = rng.normal(0, 1, n).astype(np.float32)
    b, a = butter(1, 240 / (SR / 2), btype="high")
    y = lfilter(b, a, noise).astype(np.float32)
    return _match_rms(y, -48.0)


def _fade(x: np.ndarray, ms: float = 6.0) -> np.ndarray:
    n = min(len(x) // 2, int(SR * ms / 1000))
    if n < 2:
        return x
    ramp = np.linspace(0, 1, n, dtype=np.float32)
    y = x.copy()
    y[:n] *= ramp
    y[-n:] *= ramp[::-1]
    return y


def synth_lines(spec, work: Path) -> list[dict]:
    """Return one item per line: wav path + word dicts in sentence-local time."""
    work.mkdir(parents=True, exist_ok=True)
    takes = spec.voice.get("takes") or []
    out = []
    engine = spec.voice.get("engine", "espeak")
    for i, line in enumerate(spec.lines):
        dest = work / f"s{i:02d}.wav"
        if i < len(takes) and takes[i].get("wav"):
            audio, sr = read_wav(Path(takes[i]["wav"]))
            words_path = takes[i].get("words")
            if words_path:
                words = load_words_json(Path(words_path), line.say)
            elif engine == "whisper":
                write_wav(dest, _resample(audio, sr), SR)
                words = align_whisper(dest, line.say, spec.voice.get("whisper_model", "small.en"))
                audio, sr = read_wav(dest)
            else:
                raise ValueError(f"line {i} has a wav but no word timings")
            audio = _resample(audio, sr)
        else:
            audio, sr, words = speak(line.say, spec.voice.get("voice", "en-us"), int(spec.voice.get("rate", 138)))
            audio = _resample(audio, sr)
        audio = _fade(_match_rms(audio, -20.0), 8)
        write_wav(dest, audio, SR)
        out.append({"wav": str(dest), "words": words, "audio": audio})
    return out


def assemble(spec, takes: list[dict]) -> tuple[np.ndarray, dict]:
    rng = np.random.default_rng(7)
    lead = float(spec.voice.get("lead_in", 0.12))
    tail = float(spec.voice.get("tail", 0.16))
    pieces = [_room(int(lead * SR), rng)]
    t = lead
    lines = []
    flat = []
    for i, (line, take) in enumerate(zip(spec.lines, takes)):
        audio = take["audio"]
        start = t
        words = []
        for w in take["words"]:
            item = {
                "text": w["text"],
                "start": round(start + w["start"], 4),
                "end": round(start + w["end"], 4),
                "keyword": bool(w.get("keyword", is_keyword(w["text"]))),
                "line": i,
            }
            words.append(item)
            flat.append(item)
        end = start + len(audio) / SR
        lines.append({
            "text": line.text,
            "say": line.say,
            "kind": line.kind,
            "start": round(start, 4),
            "end": round(end, 4),
            "gap": line.gap if i < len(spec.lines) - 1 else 0.0,
            "words": words,
        })
        pieces.append(audio)
        t = end
        if i < len(spec.lines) - 1:
            gap_n = int(round(line.gap * SR))
            pieces.append(_room(gap_n, rng))
            t += line.gap
    pieces.append(_room(int(tail * SR), rng))
    voice = np.concatenate(pieces).astype(np.float32)
    voice = _keyword_gain(voice, flat)
    timeline = {
        "duration": round(len(voice) / SR, 4),
        "lead_in": lead,
        "lines": lines,
        "words": flat,
        "sample_rate": SR,
    }
    return voice, timeline


def _keyword_gain(voice: np.ndarray, words: list[dict]) -> np.ndarray:
    g = np.ones(len(voice), np.float32)
    for w in words:
        if not w["keyword"]:
            continue
        a = int(w["start"] * SR)
        b = int(min(w["end"], w["start"] + 2.5) * SR)
        b = min(b, len(voice))
        if b - a < 8:
            continue
        span = min(int(0.30 * SR), b - a)
        s0 = b - span
        ramp = max(8, int(0.012 * SR))
        ramp = min(ramp, span)
        db = 8.0 if span > int(0.18 * SR) else 6.5
        gain = 10 ** (db / 20.0)
        env = np.full(span, gain, np.float32)
        env[:ramp] = np.linspace(1.0, gain, ramp, dtype=np.float32)
        g[s0:b] *= env
    out = voice * g
    peak = float(np.max(np.abs(out))) if len(out) else 0.0
    if peak > 0.89:
        out *= 0.89 / peak
    return out


def _whoosh(rng) -> np.ndarray:
    n = int(0.36 * SR)
    noise = rng.normal(0, 1, n).astype(np.float32)
    b, a = butter(2, [0.04, 0.28], btype="band")
    y = lfilter(b, a, noise).astype(np.float32)
    t = np.linspace(0, 1, n, dtype=np.float32)
    env = np.sin(np.pi * t) ** 1.4
    return y * env


def _pop(rng) -> np.ndarray:
    n = int(0.12 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    tone = np.sin(2 * np.pi * 150 * t) * np.exp(-t / 0.04)
    click = rng.normal(0, 1, n).astype(np.float32) * np.exp(-t / 0.008)
    return (tone * 0.8 + click * 0.25).astype(np.float32)


def _tick() -> np.ndarray:
    n = int(0.045 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    return (np.sin(2 * np.pi * 1600 * t) * np.exp(-t / 0.012)).astype(np.float32)


def _ding() -> np.ndarray:
    n = int(0.45 * SR)
    t = np.arange(n, dtype=np.float32) / SR
    y = (np.sin(2 * np.pi * 880 * t) + 0.45 * np.sin(2 * np.pi * 1320 * t))
    return (y * np.exp(-t / 0.18)).astype(np.float32)


def _swell(rng) -> np.ndarray:
    n = int(0.7 * SR)
    noise = rng.normal(0, 1, n).astype(np.float32)
    b, a = butter(2, 0.08)
    y = lfilter(b, a, noise).astype(np.float32)
    env = np.linspace(0, 1, n, dtype=np.float32) ** 1.4
    env[-int(0.08 * SR):] *= np.linspace(1, 0, int(0.08 * SR), dtype=np.float32)
    return y * env


def _stereo(mono: np.ndarray, delay_ms: float = 11.0) -> np.ndarray:
    d = int(SR * delay_ms / 1000)
    right = np.zeros_like(mono)
    if d < len(mono):
        right[d:] = mono[:-d] * 0.85
    left = mono
    return np.stack([left, right], axis=1)


def _place(buf: np.ndarray, sig: np.ndarray, at: float) -> None:
    a = int(at * SR)
    if a < 0:
        sig = sig[-a:]
        a = 0
    b = min(len(buf), a + len(sig))
    if a >= len(buf) or b <= a:
        return
    buf[a:b] += sig[:b - a]


def _envelope(voice: np.ndarray) -> np.ndarray:
    mag = np.abs(voice)
    # 30 ms smoother
    n = 31
    kernel = np.ones(n, np.float32) / n
    return np.convolve(mag, kernel, mode="same")


def mix(spec, voice: np.ndarray, timeline: dict) -> tuple[np.ndarray, dict]:
    rng = np.random.default_rng(11)
    n = len(voice)
    sfx_l = np.zeros(n, np.float32)
    events = []

    def add(kind: str, t: float, sig: np.ndarray):
        _place(sfx_l, sig, t)
        events.append({"kind": kind, "t": round(float(t), 3)})

    starts = [ln["start"] for ln in timeline["lines"]]
    for i, st in enumerate(starts):
        if i == 0:
            add("whoosh", 0.02, _whoosh(rng) * 0.55)
        else:
            add("whoosh", st - 0.17, _whoosh(rng))
    for w in timeline["words"]:
        if not w["keyword"]:
            continue
        kind = timeline["lines"][w["line"]]["kind"]
        if kind == "p":
            add("ding", w["start"] - 0.02, _ding() * 0.7)
        else:
            add("pop", w["start"] - 0.06, _pop(rng))
    for w in timeline["words"]:
        if any(ch.isdigit() for ch in w["text"]):
            add("tick", w["start"] - 0.04, _tick())
    add("swell", max(0.0, timeline["duration"] - 0.75), _swell(rng) * 0.8)

    env = _envelope(voice)
    voice_peak = float(np.max(np.abs(voice))) + 1e-9
    # Extra duck while the voice is up, then pin the SFX peak 12 dB under.
    duck = 1.0 / (1.0 + 6.0 * (env / voice_peak))
    sfx_l *= duck.astype(np.float32)
    sfx_peak = float(np.max(np.abs(sfx_l))) + 1e-9
    target = voice_peak * 10 ** (-12.0 / 20.0)
    sfx_l *= target / sfx_peak

    t = np.arange(n, dtype=np.float32) / SR
    sub = (0.02 * np.sin(2 * np.pi * 52 * t)).astype(np.float32)
    noise = rng.normal(0, 1, n).astype(np.float32)
    b, a = butter(2, 500 / (SR / 2))
    pad = lfilter(b, a, noise).astype(np.float32)
    pad = _match_rms(pad, -32.0)
    speech = env > (0.08 * voice_peak)
    # 14 dB down while speaking, so the bed is still audible in the gaps.
    bed_gain = np.where(speech, 10 ** (-14 / 20), 1.0).astype(np.float32)
    bed = (sub * 0.35 + pad) * bed_gain

    voice_st = np.stack([voice, voice], axis=1)
    sfx_st = _stereo(sfx_l)
    bed_st = np.stack([bed, bed * 0.92], axis=1)
    mix_st = voice_st + sfx_st + bed_st
    peak = float(np.max(np.abs(mix_st)))
    if peak > 0.9:
        mix_st *= 0.9 / peak
    mix_st = _fade(mix_st.reshape(-1), 7).reshape(-1, 2)

    def db(x):
        return round(20 * math_log10(float(np.max(np.abs(x))) + 1e-12), 2)

    def rms_db(mask, sig):
        if not np.any(mask):
            return None
        return round(20 * math_log10(_rms(sig[mask]) + 1e-12), 2)

    report = {
        "voice_peak_db": db(voice),
        "sfx_peak_db": db(sfx_l),
        "sfx_under_voice_db": round(db(voice) - db(sfx_l), 2),
        "bed_rms_speech_db": rms_db(speech, bed),
        "bed_rms_pause_db": rms_db(~speech, bed),
        "n_sfx": len(events),
        "events": events,
        "duration": timeline["duration"],
    }
    return mix_st.astype(np.float32), report


def math_log10(x: float) -> float:
    return float(np.log10(max(x, 1e-12)))


def loudnorm_two_pass(src: Path, dst: Path, tp: float = -1.5) -> dict:
    probe = _ffmpeg([
        "ffmpeg", "-hide_banner", "-i", str(src),
        "-af", f"loudnorm=I=-14:TP={tp}:LRA=11:print_format=json",
        "-f", "null", "-",
    ])
    measured = _parse_loudnorm_json(probe)
    af = (
        f"loudnorm=I=-14:TP={tp}:LRA=11:linear=true:"
        f"measured_I={measured['input_i']}:measured_TP={measured['input_tp']}:"
        f"measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}:"
        f"offset={measured['target_offset']}"
    )
    _ffmpeg([
        "ffmpeg", "-y", "-hide_banner", "-i", str(src),
        "-af", af, "-ar", str(SR), "-ac", "2", str(dst),
    ])
    return measured


def measure_wav(path: Path) -> dict:
    text = _ffmpeg([
        "ffmpeg", "-hide_banner", "-i", str(path),
        "-af", "ebur128=peak=true", "-f", "null", "-",
    ])
    return _parse_ebur128(text)


def _parse_loudnorm_json(text: str) -> dict:
    start = text.rfind("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise RuntimeError("loudnorm did not return JSON:\n" + text[-1500:])
    return json.loads(text[start:end + 1])


def _parse_ebur128(text: str) -> dict:
    integrated = None
    true_peak = None
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("I:") and "LUFS" in s:
            integrated = float(s.split()[1])
        if s.startswith("Peak:") and "dBFS" in s:
            true_peak = float(s.split()[1])
    if integrated is None or true_peak is None:
        raise RuntimeError("could not parse ebur128:\n" + text[-1500:])
    return {"lufs": integrated, "tp": true_peak}


def _ffmpeg(cmd: list[str]) -> str:
    r = subprocess.run(cmd, capture_output=True, text=True)
    blob = (r.stderr or "") + (r.stdout or "")
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg failed ({r.returncode}):\n" + blob[-2000:])
    return blob


def mux(video: Path, wav: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    _ffmpeg([
        "ffmpeg", "-y", "-hide_banner",
        "-i", str(video), "-i", str(wav),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "320k", "-ar", str(SR), "-ac", "2",
        "-movflags", "+faststart",
        str(dest),
    ])

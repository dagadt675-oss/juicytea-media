"""Word times from the mapped v4 narration.

The shipped picture is silent. Downstream adds ElevenLabs and karaoke.
assemble() is not called by make.py.
"""

from __future__ import annotations

import json
import subprocess
import wave
from pathlib import Path

import numpy as np

SR = 48000
ASSETS = Path(__file__).resolve().parent / "assets"
V4 = ASSETS / "v4_audio.wav"

# Display tokens, in order. Punctuation is what the caption shows.
SCRIPT = [
    "I", "turned", "Earth", "into", "an", "American", "football.",
    "The", "North", "Pole", "is", "now", "in", "space.",
    "Sorry,", "Santa.",
    "Your", "workshop", "is", "now", "in", "space.",
    "Oceans?", "They", "slide.",
    "Plot", "twist:", "Earth", "is", "already",
    "forty-three", "kilometers",
    "fatter", "than", "it", "is", "tall.",
    "It's", "basically", "a", "football...",
    "that", "someone", "sat", "on.",
]


def _read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path)) as w:
        ch = w.getnchannels()
        sr = w.getframerate()
        n = w.getnframes()
        raw = w.readframes(n)
        sw = w.getsampwidth()
    if sw != 2:
        raise RuntimeError(f"expected 16-bit wav, got {sw}")
    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0
    x = x.reshape(-1, ch)
    if sr != SR:
        raise RuntimeError(f"expected {SR} Hz, got {sr}")
    if ch == 1:
        x = np.repeat(x, 2, axis=1)
    return x


def _write_wav(path: Path, x: np.ndarray) -> None:
    y = np.clip(x, -1, 1)
    pcm = (y * 32767.0).astype(np.int16)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as w:
        w.setnchannels(pcm.shape[1] if pcm.ndim == 2 else 1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def _atempo(x: np.ndarray, rate: float) -> np.ndarray:
    """rate < 1 slows the clip (ffmpeg atempo). Pitch stays put."""
    if abs(rate - 1.0) < 1e-3:
        return x
    tmp_in = Path("/tmp/s15_at_in.wav")
    tmp_out = Path("/tmp/s15_at_out.wav")
    _write_wav(tmp_in, x)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(tmp_in),
         "-af", f"atempo={rate}", str(tmp_out)],
        check=True,
    )
    return _read_wav(tmp_out)


def _xfade(a: np.ndarray, b: np.ndarray, n: int) -> np.ndarray:
    n = int(min(n, len(a) // 2, max(1, len(b) // 2)))
    if n < 2:
        return np.concatenate([a, b], axis=0)
    ramp = np.linspace(0, 1, n, dtype=np.float32)[:, None]
    mid = a[-n:] * (1 - ramp) + b[:n] * ramp
    return np.concatenate([a[:-n], mid, b[n:]], axis=0)


def _concat(pieces: list[np.ndarray], xfade_ms: float = 12.0) -> np.ndarray:
    n = int(SR * xfade_ms / 1000)
    out = pieces[0]
    for p in pieces[1:]:
        out = _xfade(out, p, n)
    return out.astype(np.float32)


def _slice(x: np.ndarray, a: float, b: float) -> np.ndarray:
    return x[int(a * SR):int(b * SR)].copy()


def _room(x: np.ndarray, seconds: float) -> np.ndarray:
    """Loop a quiet bit of the original floor so pauses are not digital zeros."""
    seed = _slice(x, 4.50, 4.68)
    # High-pass-ish: remove DC.
    seed = seed - seed.mean(axis=0, keepdims=True)
    need = int(seconds * SR)
    if need <= 0:
        return np.zeros((0, x.shape[1]), np.float32)
    reps = int(np.ceil(need / len(seed))) + 1
    tiled = np.tile(seed, (reps, 1))[:need]
    # Fade the loop seam inside the seed so a tiled pause doesn't tick.
    k = min(len(seed) // 4, 200)
    return tiled


def _repair_santa(x: np.ndarray) -> np.ndarray:
    """Join the stressed onset of 'Santa' to its vowel and drop the extra 'n'.

    v4 says the name as San-nta: a clean attack, a second nasal bump, then the
    vowel, then a quiet orphan burst vosk does not even hear as a word.
    """
    attack = _slice(x, 5.345, 5.430)
    vowel = _slice(x, 5.545, 5.690)
    word = _xfade(attack, vowel, int(0.022 * SR))
    # Match the emphasis already on "Sorry" (that word peaks near -11 dBFS).
    sorry = _slice(x, 4.96, 5.18)
    def rms(a):
        return float(np.sqrt(np.mean(a ** 2)) + 1e-9)
    gain = min(2.2, (rms(sorry) * 0.92) / rms(word))
    word *= np.float32(gain)
    # 8 ms edges so the splice does not click against the room.
    n = int(0.008 * SR)
    ramp = np.linspace(0, 1, n, dtype=np.float32)[:, None]
    word[:n] *= ramp
    word[-n:] *= ramp[::-1]
    return word


def _voice_gate(x: np.ndarray) -> np.ndarray:
    """1 while speech (or a loud hit) is up, with a hold so the bed stays ducked."""
    mono = x.mean(axis=1)
    hop = int(0.01 * SR)
    rms = np.array([
        np.sqrt(np.mean(mono[i:i + hop] ** 2) + 1e-12)
        for i in range(0, len(mono) - hop, hop)
    ], np.float32)
    db = 20 * np.log10(rms + 1e-9)
    raw = db > -27.0
    # Hold 140 ms after speech so gaps inside a sentence stay ducked.
    hold = 14
    gate = raw.copy()
    last = -10_000
    for i, v in enumerate(raw):
        if v:
            last = i
        elif i - last < hold:
            gate[i] = True
    # Expand hop gate to samples.
    up = np.repeat(gate, hop).astype(np.float32)
    if len(up) < len(x):
        up = np.pad(up, (0, len(x) - len(up)))
    return up[:len(x)]


def _bed(n: int, gate: np.ndarray) -> np.ndarray:
    """D-minor eighth-note pluck. A pattern, not a noise rumble."""
    t = np.arange(n, dtype=np.float32) / SR
    bpm = 96.0
    step = 60.0 / bpm / 2.0  # eighth
    # D F A C — a repeating figure.
    freqs = np.array([73.42, 87.31, 110.00, 130.81, 146.83, 110.00, 87.31, 73.42], np.float32)
    idx = (t / step).astype(np.int32) % len(freqs)
    f = freqs[idx]
    pos = np.mod(t, step)
    env = np.exp(-pos / 0.09).astype(np.float32) * np.clip(1 - pos / (step * 0.92), 0, 1)
    # Integrate frequency for a continuous phase so notes don't click.
    phase = np.cumsum(f / SR) * (2 * np.pi)
    pluck = np.sin(phase) * env
    # Soft knock on the downbeat, tucked under the pluck.
    beat = 60.0 / bpm
    bpos = np.mod(t, beat)
    knock = np.sin(2 * np.pi * (90 * np.exp(-bpos / 0.03)) * t) * np.exp(-bpos / 0.045)
    knock *= (bpos < 0.12).astype(np.float32)
    mono = (pluck * 0.72 + knock * 0.18).astype(np.float32)
    peak = np.max(np.abs(mono)) + 1e-9
    mono *= np.float32(0.13 / peak)  # unducked peak about -18 dBFS
    ducked = mono * (0.20 + 0.80 * (1.0 - gate))  # about -14 dB under speech
    # Tiny Haas spread so it is not a mono pin.
    delay = int(0.011 * SR)
    right = np.concatenate([np.zeros(delay, np.float32), ducked[:-delay]])
    stereo = np.stack([ducked, right * 0.9], axis=1)
    return stereo


def _fade_ends(x: np.ndarray, ms: float = 18.0) -> np.ndarray:
    """Fade only the tail. The head stays on the first syllable."""
    y = x.copy()
    n = min(len(y) // 4, int(SR * ms / 1000))
    ramp = np.linspace(1, 0, n, dtype=np.float32)[:, None]
    y[-n:] *= ramp
    return y


# v4 word timings (vosk on the untouched mix). "in space", "now" and
# "basically" are splits the small model swallowed into a neighbour.
_V4_WORDS = [
    ("I", 0.03, 0.15),
    ("turned", 0.15, 0.42),
    ("Earth", 0.51, 0.84),
    ("into", 0.84, 1.11),
    ("an", 1.11, 1.20),
    ("American", 1.20, 1.74),
    ("football.", 1.74, 2.28),
    ("The", 2.91, 3.00),
    ("North", 3.00, 3.24),
    ("Pole", 3.24, 3.48),
    ("is", 3.48, 3.60),
    ("now", 3.60, 3.81),
    ("in", 3.81, 4.08),
    ("space.", 4.08, 4.44),
    ("Sorry,", 4.83, 5.21),
    ("Santa.", 5.34, 5.70),
    ("Your", 6.12, 6.27),
    ("workshop", 6.27, 6.75),
    ("is", 6.75, 6.84),
    ("now", 6.84, 6.96),
    ("in", 6.96, 7.10),
    ("space.", 7.10, 7.41),
    ("Oceans?", 7.80, 8.34),
    ("They", 8.88, 9.06),
    ("slide.", 9.06, 9.63),
    ("Plot", 10.11, 10.35),
    ("twist:", 10.35, 10.77),
    ("Earth", 11.07, 11.31),
    ("is", 11.31, 11.46),
    ("already", 11.46, 11.88),
    ("forty-three", 11.88, 12.54),
    ("kilometers", 12.54, 13.14),
    ("fatter", 13.17, 13.50),
    ("than", 13.50, 13.68),
    ("it", 13.68, 13.77),
    ("is", 13.77, 13.95),
    ("tall.", 13.95, 14.43),
    ("It's", 15.06, 15.22),
    ("basically", 15.22, 15.50),
    ("a", 15.50, 15.58),
    ("football...", 15.58, 15.84),
    ("that", 16.20, 16.38),
    ("someone", 16.38, 16.71),
    ("sat", 16.71, 17.00),
    ("on.", 17.00, 17.22),
]


def _lay(pieces: list[dict], xfade_ms: float = 10.0) -> tuple[np.ndarray, list[dict]]:
    """Concatenate clips and record where each source range landed."""
    n = int(SR * xfade_ms / 1000)
    out = None
    placed = []
    for p in pieces:
        clip = p["audio"]
        if out is None:
            dst0 = 0.0
            out = clip
        else:
            before = len(out)
            out = _xfade(out, clip, n)
            dst0 = (before - min(n, before // 2, len(clip) // 2)) / SR
        placed.append({
            "src": p.get("src"),
            "rate": p.get("rate", 1.0),
            "dst0": dst0,
            "dst1": len(out) / SR,
        })
    return out.astype(np.float32), placed


def _warp(placed: list[dict]) -> list[dict]:
    words = []
    for text, a, b in _V4_WORDS:
        hit = None
        for seg in placed:
            src = seg["src"]
            if src is None:
                continue
            if src[0] - 1e-3 <= a and b <= src[1] + 1e-3:
                hit = seg
                break
        if hit is None:
            raise RuntimeError(f"no segment covers {text} {a:.2f}-{b:.2f}")
        rate = hit["rate"]
        words.append({
            "text": text,
            "start": round(hit["dst0"] + (a - hit["src"][0]) / rate, 4),
            "end": round(hit["dst0"] + (b - hit["src"][0]) / rate, 4),
        })
    return words


def assemble(work: Path) -> tuple[np.ndarray, dict, list[dict]]:
    src = _read_wav(V4)
    # First-syllable check: the vowel of "I" is already on the opening samples.
    head = src[: int(0.04 * SR)]
    head_db = 20 * np.log10(float(np.sqrt(np.mean(head ** 2))) + 1e-9)
    if head_db < -28:
        raise RuntimeError(f"opening is quiet ({head_db:.1f} dB); refusing to ship dead air")

    santa = _atempo(_repair_santa(src), 0.90)
    sorry = _atempo(_slice(src, 4.83, 5.22), 0.90)
    forty = _atempo(_slice(src, 11.88, 13.14), 0.89)  # ~12% slower
    fatter = _atempo(_slice(src, 13.17, 13.50), 0.88)

    pieces = [
        {"audio": _slice(src, 0.00, 4.83), "src": (0.00, 4.83), "rate": 1.0},
        {"audio": sorry, "src": (4.83, 5.22), "rate": 0.90},
        {"audio": _room(src, 0.06), "src": None, "rate": 1.0},
        {"audio": santa, "src": (5.34, 5.70), "rate": (5.70 - 5.34) / (len(santa) / SR)},
        {"audio": _room(src, 0.16), "src": None, "rate": 1.0},
        {"audio": _slice(src, 6.12, 11.88), "src": (6.12, 11.88), "rate": 1.0},
        {"audio": _room(src, 0.12), "src": None, "rate": 1.0},
        {"audio": forty, "src": (11.88, 13.14), "rate": 0.89},
        {"audio": _room(src, 0.11), "src": None, "rate": 1.0},
        {"audio": fatter, "src": (13.17, 13.50), "rate": 0.88},
        {"audio": _slice(src, 13.50, src.shape[0] / SR), "src": (13.50, src.shape[0] / SR), "rate": 1.0},
    ]
    voice, placed = _lay(pieces, 10.0)
    words = _warp(placed)
    gate = _voice_gate(voice)
    bed = _bed(len(voice), gate)
    mix = voice + bed
    mix = _fade_ends(mix, 22.0)
    # Leave headroom for the loudnorm pass.
    peak = float(np.max(np.abs(mix)))
    if peak > 0.89:
        mix *= np.float32(0.89 / peak)

    work.mkdir(parents=True, exist_ok=True)
    _write_wav(work / "voice.wav", _fade_ends(voice, 22.0))
    premix = work / "premix.wav"
    _write_wav(premix, mix)
    final = work / "mix.wav"
    _loudnorm(premix, final)
    out = _read_wav(final)
    meta = {
        "head_db": round(head_db, 2),
        "samples": int(len(out)),
        "seconds": round(len(out) / SR, 4),
        "santa_gain_note": "rejoined onset+vowel, matched to Sorry, orphan burst removed",
        "pauses_s": {"before_forty_three": 0.12, "before_fatter": 0.11},
        "slow": {"sorry": 0.90, "santa": 0.90, "forty_three_kilometers": 0.89, "fatter": 0.88},
    }
    return out, meta, words


def _loudnorm(src: Path, dest: Path) -> None:
    probe = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(src),
         "-af", "loudnorm=I=-14:TP=-1.8:LRA=11:print_format=json",
         "-f", "null", "-"],
        capture_output=True, text=True,
    )
    blob = probe.stderr
    jtxt = blob[blob.rfind("{") : blob.rfind("}") + 1]
    measured = json.loads(jtxt)
    af = (
        "loudnorm=I=-14:TP=-1.8:LRA=11:"
        f"measured_I={measured['input_i']}:measured_TP={measured['input_tp']}:"
        f"measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}:"
        f"offset={measured['target_offset']}:linear=true:print_format=summary"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-af", af,
         "-ar", str(SR), "-ac", "2", str(dest)],
        check=True,
    )


def align_words(wav: Path) -> list[dict]:
    """Map the script onto a vosk pass of the finished mix."""
    import os
    os.environ.setdefault("VOSK_MODEL", "/tmp/vosk/model")
    from vosk import KaldiRecognizer, Model

    pcm = Path("/tmp/s15_align.wav")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", "16000", str(pcm)],
        check=True,
    )
    model = Model(os.environ["VOSK_MODEL"])
    wf = wave.open(str(pcm))
    rec = KaldiRecognizer(model, 16000)
    rec.SetWords(True)
    heard = []
    while True:
        data = wf.readframes(4000)
        if not data:
            break
        if rec.AcceptWaveform(data):
            heard.extend(json.loads(rec.Result()).get("result") or [])
    heard.extend(json.loads(rec.FinalResult()).get("result") or [])

    def norm(w: str) -> str:
        return "".join(ch for ch in w.lower() if ch.isalpha())

    # Fold "forty"+"three" if the model splits the number.
    folded = []
    i = 0
    while i < len(heard):
        w = heard[i]["word"]
        if w == "forty" and i + 1 < len(heard) and heard[i + 1]["word"] in {"three", "3"}:
            folded.append({
                "word": "fortythree",
                "start": heard[i]["start"],
                "end": heard[i + 1]["end"],
            })
            i += 2
            continue
        folded.append(heard[i])
        i += 1

    aliases = {
        "football": "football",
        "fortythree": "fortythree",
        "kilometers": "kilometers",
        "kilometres": "kilometers",
        "its": "its",
        "oceans": "oceans",
        "ocean": "oceans",
    }
    hwords = []
    for h in folded:
        key = aliases.get(h["word"], norm(h["word"]))
        hwords.append({**h, "key": key})

    used = [False] * len(hwords)
    out = []
    cursor = 0
    for token in SCRIPT:
        key = norm(token).replace("fortythree", "fortythree")
        if key == "fortythree":
            key = "fortythree"
        key = key.replace("-", "")
        if token.startswith("forty"):
            key = "fortythree"
        found = None
        for j in range(cursor, len(hwords)):
            if used[j]:
                continue
            hk = hwords[j]["key"].replace("-", "")
            if hk == key or (key.startswith(hk) and len(hk) >= 4) or (hk.startswith(key) and len(key) >= 4):
                found = j
                break
        if found is None:
            out.append({"text": token, "start": None, "end": None})
            continue
        used[found] = True
        cursor = found + 1
        out.append({
            "text": token,
            "start": float(hwords[found]["start"]),
            "end": float(hwords[found]["end"]),
        })

    # Fill anything vosk swallowed (the small model drops "in", "now", "basically")
    # by sharing the gap between the nearest anchored neighbours.
    known = [i for i, w in enumerate(out) if w["start"] is not None]
    if not known:
        raise RuntimeError("alignment produced no words")
    for i, w in enumerate(out):
        if w["start"] is not None:
            continue
        prev_i = max((k for k in known if k < i), default=None)
        next_i = min((k for k in known if k > i), default=None)
        if prev_i is None:
            w["start"] = max(0.0, out[next_i]["start"] - 0.18)
            w["end"] = out[next_i]["start"]
        elif next_i is None:
            w["start"] = out[prev_i]["end"]
            w["end"] = out[prev_i]["end"] + 0.22
        else:
            gap_a = out[prev_i]["end"]
            gap_b = out[next_i]["start"]
            if gap_b < gap_a + 0.04:
                # Neighbours are flush: steal a slice from the longer one.
                gap_a = max(out[prev_i]["start"], out[prev_i]["end"] - 0.12)
                gap_b = gap_a + 0.12
                out[prev_i]["end"] = gap_a
            w["start"] = gap_a
            w["end"] = gap_b
        known.append(i)
        known.sort()
    # If several missing tokens share one gap, split it.
    i = 0
    while i < len(out):
        if i > 0 and out[i]["start"] == out[i - 1]["start"] and out[i]["end"] == out[i - 1]["end"]:
            j = i
            while j < len(out) and out[j]["start"] == out[i]["start"]:
                j += 1
            a, b = out[i]["start"], out[i]["end"]
            step = (b - a) / max(1, j - i)
            for k, idx in enumerate(range(i, j)):
                out[idx]["start"] = round(a + step * k, 4)
                out[idx]["end"] = round(a + step * (k + 1), 4)
            i = j
        else:
            out[i]["start"] = round(float(out[i]["start"]), 4)
            out[i]["end"] = round(float(out[i]["end"]), 4)
            i += 1
    return out

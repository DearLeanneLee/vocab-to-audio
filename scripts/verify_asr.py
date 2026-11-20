"""Spot-check generated audio by transcribing each spoken segment (needs the optional
SenseVoice model). Rare English words are often misspelled by the recognizer: use this
to catch missing or garbled segments, not to judge pronunciation.

Usage: python scripts/verify_asr.py out/wav/0001.wav out/wav/0002.wav ...
"""
import os, sys, glob
import numpy as np, soundfile as sf, sherpa_onnx
M = os.environ.get("MODELS_DIR", os.path.join(os.path.dirname(__file__), "..", "models"))
d = glob.glob(f"{M}/sherpa-onnx-sense-voice*")[0]
rec = sherpa_onnx.OfflineRecognizer.from_sense_voice(model=f"{d}/model.int8.onnx", tokens=f"{d}/tokens.txt", use_itn=True)

def segments(x, sr, min_gap=0.22):
    env = np.convolve(np.abs(x), np.ones(480) / 480, "same"); quiet = env < 0.003
    segs, start, run, hop = [], None, 0, 240
    for i in range(0, len(x), hop):
        if not quiet[i]:
            if start is None: start = i
            run = 0
        elif start is not None:
            run += hop
            if run > sr * min_gap: segs.append((start, i)); start, run = None, 0
    if start is not None: segs.append((start, len(x)))
    return segs

for f in sys.argv[1:]:
    x, sr = sf.read(f, dtype="float32")
    out = []
    for s, e in segments(x, sr):
        st = rec.create_stream(); st.accept_waveform(sr, x[s:e]); rec.decode_stream(st); out.append(st.result.text)
    print(os.path.basename(f), f"{len(x)/sr:.1f}s |", " / ".join(out))

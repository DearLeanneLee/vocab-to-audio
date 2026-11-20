"""抽查生成的音频：把每一段语音转写成文字（需要可选的 SenseVoice 模型）。
语音识别经常拼错生僻英文单词，所以它适合发现漏读、乱读，不能用来判断发音是否准确。
Spot-check generated audio by transcribing each spoken segment (needs the optional
SenseVoice model). The recognizer often misspells rare English words: use this to
catch missing or garbled segments, not to judge pronunciation.

用法 / Usage: python scripts/verify_asr.py out/wav/0001.wav out/wav/0002.wav ...
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

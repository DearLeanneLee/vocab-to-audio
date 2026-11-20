"""语音引擎：英文用 Kokoro，中文用 MeloTTS，都通过 sherpa-onnx 运行。
Speech engines: Kokoro (English) and MeloTTS (Chinese), both run via sherpa-onnx.
"""
import os, glob
from math import gcd
import numpy as np
import sherpa_onnx
from scipy.signal import resample_poly

MODELS = os.environ.get("MODELS_DIR", os.path.join(os.path.dirname(__file__), "..", "models"))
SR = 24000
EN_SPEAKER = int(os.environ.get("EN_SPEAKER", 3))   # 3 = af_heart（kokoro-multi-lang-v1_0 中的编号 / speaker ID in kokoro-multi-lang-v1_0）
_cache = {}

def _kokoro():
    if "kokoro" not in _cache:
        m = f"{MODELS}/kokoro-multi-lang-v1_0"
        _cache["kokoro"] = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
                    model=f"{m}/model.onnx", voices=f"{m}/voices.bin", tokens=f"{m}/tokens.txt",
                    data_dir=f"{m}/espeak-ng-data", dict_dir=f"{m}/dict",
                    lexicon=f"{m}/lexicon-us-en.txt,{m}/lexicon-zh.txt"),
                num_threads=os.cpu_count() or 2),
            max_num_sentences=1))
    return _cache["kokoro"]

def _melo():
    if "melo" not in _cache:
        m = f"{MODELS}/vits-melo-tts-zh_en"
        _cache["melo"] = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                    model=f"{m}/model.onnx", lexicon=f"{m}/lexicon.txt",
                    tokens=f"{m}/tokens.txt", dict_dir=f"{m}/dict"),
                num_threads=os.cpu_count() or 2),
            rule_fsts=f"{m}/date.fst,{m}/phone.fst,{m}/number.fst,{m}/new_heteronym.fst",
            max_num_sentences=1))
    return _cache["melo"]

def _to24k(x, sr):
    if sr == SR:
        return x.astype(np.float32)
    g = gcd(SR, sr)
    return resample_poly(x, SR // g, sr // g).astype(np.float32)

def normalize(x, peak=0.8):
    return (x / max(1e-6, float(np.abs(x).max())) * peak).astype(np.float32)

def english(text, speed=0.9):
    a = _kokoro().generate(text, sid=EN_SPEAKER, speed=speed)
    return normalize(_to24k(np.array(a.samples, np.float32), a.sample_rate))

def chinese(text, speed=1.0):
    a = _melo().generate(text, sid=0, speed=speed)
    return normalize(_to24k(np.array(a.samples, np.float32), a.sample_rate))

# ---- 引导语技巧 / lead-in trick -------------------------------------------
# MeloTTS 单独读很短的内容（比如两个字的词）时经常含糊。
# 做法：先合成「意思是<中文意思>」，用语音识别模型的时间戳找到「意思是」
# 结束的位置，再把它剪掉。需要安装可选的语音识别模型。
# MeloTTS garbles very short inputs (e.g. a two-character word read alone).
# We synthesize "意思是<meaning>", locate where "意思是" ends using the ASR
# model's token timestamps, and cut it off. Requires the optional ASR model.
_rec = None
def _recognizer():
    global _rec
    if _rec is None:
        hits = glob.glob(f"{MODELS}/sherpa-onnx-sense-voice*")
        if not hits:
            return None
        d = hits[0]
        _rec = sherpa_onnx.OfflineRecognizer.from_sense_voice(
            model=f"{d}/model.int8.onnx", tokens=f"{d}/tokens.txt", use_itn=False)
    return _rec

LEAD_IN = "意思是"
_SHI_LIKE = set("是事时式私此四士世诗市示十")

def chinese_meaning(text):
    """清晰地读出一个中文意思。返回（音频，是否用了引导语技巧）。
    Read a Chinese meaning clearly. Returns (audio, used_lead_in_trick).
    """
    rec = _recognizer()
    if rec is None:
        return chinese(text), False
    x = chinese(LEAD_IN + text)
    st = rec.create_stream(); st.accept_waveform(SR, x); rec.decode_stream(st)
    toks, ts = st.result.tokens, st.result.timestamps
    idx = next((i for i, t in enumerate(toks[:5]) if t in _SHI_LIKE), None)
    if idx is None or idx + 1 >= len(ts):
        return chinese(text), False
    start = int((ts[idx + 1] + 0.01) * SR)
    y = x[start:].copy()
    n = min(360, len(y)); y[:n] *= np.linspace(0, 1, n)   # 短淡入 / short fade-in
    return y, True

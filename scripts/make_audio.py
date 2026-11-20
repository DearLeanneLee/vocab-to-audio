"""Generate one WAV per word from a CSV.

CSV columns (header required): n, group, word, synonyms, meaning
Each entry is read as:  "<n>. <word>."  ->  <Chinese meaning>  ->  "Synonyms: <synonyms>."

Usage: python scripts/make_audio.py words.csv out/wav [first] [last]
Re-running skips entries that already exist, so it can be resumed.
"""
import csv, os, sys
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(__file__))
from engines import english, chinese_meaning, SR
from text_clean import zh_clean, en_clean

def gap(sec): return np.zeros(int(SR * sec), np.float32)

def main(csv_path, out_dir, first=1, last=10**9):
    os.makedirs(out_dir, exist_ok=True)
    rows = list(csv.DictReader(open(csv_path, encoding="utf-8-sig")))
    fallback = []
    for r in rows:
        n = int(r["n"])
        if not (first <= n <= last):
            continue
        dst = f"{out_dir}/{n:04d}.wav"
        if os.path.exists(dst):
            continue
        p1 = english(f"{n}. {en_clean(r['word'])}.", speed=0.88)
        p2, ok = chinese_meaning(zh_clean(r["meaning"]))
        if not ok:
            fallback.append(n)
        parts = [p1, gap(0.45), p2]
        if r.get("synonyms", "").strip():
            parts += [gap(0.45), english("Synonyms: " + en_clean(r["synonyms"]) + ".", speed=0.95)]
        sf.write(dst + ".tmp.wav", np.concatenate(parts), SR)
        os.replace(dst + ".tmp.wav", dst)
        print(n, r["word"], flush=True)
    if fallback:
        print("Lead-in trick not applied (meaning read directly):", fallback)

if __name__ == "__main__":
    a = sys.argv
    main(a[1], a[2], int(a[3]) if len(a) > 3 else 1, int(a[4]) if len(a) > 4 else 10**9)

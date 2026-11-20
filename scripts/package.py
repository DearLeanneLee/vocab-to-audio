"""把 WAV 打包成：每个单词一个 MP3（压缩包，按组分文件夹）、每组一个合集 MP3、一份编号词表（xlsx）。需要 ffmpeg。
Package WAVs into: one MP3 per word (zipped, one folder per group), one combined MP3 per group,
and a numbered word list (xlsx). Requires ffmpeg.

用法 / Usage: python scripts/package.py words.csv out/wav out/release
"""
import csv, os, re, subprocess, sys, zipfile
import numpy as np, soundfile as sf
from openpyxl import Workbook

def safe(s): return re.sub(r"[^0-9A-Za-z]+", "_", s).strip("_")
def mp3(src, dst, title):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-ac", "1", "-b:a", "64k",
                    "-metadata", f"title={title}", dst], check=True)

def main(csv_path, wav_dir, out):
    rows = list(csv.DictReader(open(csv_path, encoding="utf-8-sig")))
    os.makedirs(f"{out}/mp3", exist_ok=True)
    groups = {}
    for r in rows:
        n = int(r["n"]); name = f"{n:04d}_{safe(r['word'])}.mp3"; r["file"] = name
        mp3(f"{wav_dir}/{n:04d}.wav", f"{out}/mp3/{name}", f"{n} {r['word']}")
        groups.setdefault(r.get("group") or "all", []).append(r)
    with zipfile.ZipFile(f"{out}/per_word_mp3.zip", "w") as z:
        for g, rs in groups.items():
            for r in rs:
                z.write(f"{out}/mp3/{r['file']}", f"per_word_mp3/{g}/{r['file']}")
    for g, rs in groups.items():
        parts = []
        for r in rs:
            x, sr = sf.read(f"{wav_dir}/{int(r['n']):04d}.wav", dtype="float32")
            parts += [x, np.zeros(int(sr * 1.2), np.float32)]
        tmp = f"{out}/_{safe(g) or 'group'}.wav"; sf.write(tmp, np.concatenate(parts), sr)
        mp3(tmp, f"{out}/{g}_{rs[0]['n']}-{rs[-1]['n']}.mp3", g); os.remove(tmp)
    wb = Workbook(); ws = wb.active; ws.append(["n", "group", "word", "synonyms", "meaning", "audio file"])
    for r in rows: ws.append([int(r["n"]), r.get("group"), r["word"], r.get("synonyms"), r["meaning"], r["file"]])
    wb.save(f"{out}/word_list.xlsx")
    print("完成 / Done:", out)

if __name__ == "__main__":
    main(*sys.argv[1:4])

"""Optional: pull a 3-column word table (word | synonyms | Chinese meaning) out of a PDF
whose Chinese text can't be copied (common with scanned or oddly-encoded PDFs).

It renders each page, OCRs each column with Tesseract (eng + chi_sim), and groups text
into rows by vertical position. Column x-ranges are given as fractions of page width;
adjust them for your PDF. ALWAYS proofread the CSV it writes — OCR makes mistakes,
especially in Chinese.

Usage: python scripts/extract_pdf_table.py book.pdf words.csv --cols 0.153,0.329 0.335,0.66 0.665,0.853
Needs: poppler-utils (pdftoppm), tesseract with chi_sim.
"""
import argparse, csv, io, os, re, subprocess, tempfile
from PIL import Image

def ocr_lines(img, lang):
    out = subprocess.run(["tesseract", img, "-", "-l", lang, "--psm", "6", "tsv"],
                         capture_output=True, text=True).stdout
    lines = {}
    for d in csv.DictReader(io.StringIO(out), delimiter="\t", quoting=csv.QUOTE_NONE):
        if d["level"] != "5" or not d["text"].strip():
            continue
        k = (d["block_num"], d["par_num"], d["line_num"])
        L = lines.setdefault(k, {"y": int(d["top"]), "w": []})
        L["y"] = min(L["y"], int(d["top"])); L["w"].append((int(d["left"]), d["text"]))
    return sorted((L["y"], " ".join(t for _, t in sorted(L["w"]))) for L in lines.values())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf"); ap.add_argument("out_csv")
    ap.add_argument("--cols", nargs=3, required=True, help="x0,x1 fractions for word, synonyms, meaning")
    ap.add_argument("--dpi", type=int, default=200)
    a = ap.parse_args()
    cols = [tuple(map(float, c.split(","))) for c in a.cols]
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdftoppm", "-r", str(a.dpi), "-png", a.pdf, f"{tmp}/p"], check=True)
        for page in sorted(f for f in os.listdir(tmp) if f.endswith(".png")):
            im = Image.open(f"{tmp}/{page}"); W, H = im.size
            cut = []
            for i, (x0, x1) in enumerate(cols):
                p = f"{tmp}/c{i}.png"; im.crop((int(x0 * W), 0, int(x1 * W), H)).save(p); cut.append(p)
            words = [(y, t) for y, t in ocr_lines(cut[0], "eng") if re.fullmatch(r"[A-Za-z][A-Za-z \-]*", t)]
            syns = ocr_lines(cut[1], "eng"); mean = ocr_lines(cut[2], "chi_sim")
            for k, (y, w) in enumerate(words):
                ny = words[k + 1][0] if k + 1 < len(words) else H
                pick = lambda L, sep: sep.join(t for yy, t in L if y - 15 <= yy < ny - 15)
                m = pick(mean, "").replace(" ", "")
                if not m or "解释" in m:      # skip table header rows
                    continue
                rows.append([w.strip(), pick(syns, " "), m])
    with open(a.out_csv, "w", newline="", encoding="utf-8-sig") as f:
        wr = csv.writer(f); wr.writerow(["n", "group", "word", "synonyms", "meaning"])
        for i, r in enumerate(rows, 1):
            wr.writerow([i, ""] + r)
    print(f"Wrote {len(rows)} rows to {a.out_csv}. Proofread before generating audio!")

if __name__ == "__main__":
    main()

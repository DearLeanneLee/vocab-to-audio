# vocab-to-audio · wordlist-to-mp3

**单词表一键转 MP3，用耳朵背单词 / Turn any word list into MP3 and learn vocabulary by ear**

有些人看十遍记不住的单词，听三遍就记住了。如果你也是"耳朵比眼睛好使"的人，这个工具就是为你做的：把单词表（单词 + 等价词 + 中文意思）批量转成音频，通勤、散步、做饭、睡前都能听，把零碎时间变成背单词的时间。GRE、托福、雅思都适用。

Some people can stare at a word ten times and forget it, yet remember it after hearing it three times. If you learn better by listening than by reading, this tool is for you: it turns a vocabulary list (word + synonyms + Chinese meaning) into audio you can play on your commute, on a walk, while cooking or before bed, so spare minutes become study time. Works for GRE, TOEFL, IELTS and more.

- 🎧 **边听边背 / Learn hands-free**：英文单词 → 中文意思 → 同义词，一个词约 5 秒。 / English word → Chinese meaning → synonyms, about 5 seconds per word.
- 📦 **随用随取 / Your choice of format**：每个单词一个 MP3，或者每天一个合集从头听到尾。 / One MP3 per word, or one combined track per day.
- 💻 **完全离线、免费 / Free and offline**：本地 CPU 运行，不需要显卡，不需要付费 API。 / Runs on your own CPU, no GPU or paid API needed.

---

## 效果 / What you get

每个单词读成一段，大约 5 秒：

Each word becomes one short clip, about 5 seconds long:

> **"1. mitigate."**（英文女声 / English voice）→ **"缓和"**（中文女声 / Chinese voice）→ **"Synonyms: abate, curtail, temper, ameliorate."**（英文女声 / English voice）

输出三样东西 / Three outputs:

| 文件 / File | 说明 / Description |
|---|---|
| `per_word_mp3.zip` | 每个单词一个 MP3，按编号命名，按组（比如按天）分文件夹<br>One MP3 per word, numbered, in one folder per group (e.g. per day) |
| `<组名>_<起>-<止>.mp3`<br>`<group>_<first>-<last>.mp3` | 每组一个合集 MP3，单词之间停顿 1.2 秒，适合通勤从头听<br>One combined MP3 per group, with a 1.2 s pause between words, for listening straight through |
| `word_list.xlsx` | 编号词表，每行对应的音频文件名<br>Numbered word list with the audio filename for each row |

---

## 流程 / Workflow

```
PDF / Excel 单词表  (word list)
   │  ① 整理成 CSV（可选：用 OCR 从 PDF 提取，然后人工校对）
   │     Prepare a CSV (optional: OCR it out of a PDF, then proofread)
   ▼
words.csv  (n, group, word, synonyms, meaning)
   │  ② 逐个生成音频（英文 Kokoro + 中文 MeloTTS）
   │     Generate audio for each word (English: Kokoro, Chinese: MeloTTS)
   ▼
out/wav/0001.wav …
   │  ③ 抽查（可选：语音识别转写，检查有没有漏读、错读）
   │     Spot-check (optional: transcribe with speech recognition)
   │  ④ 打包成 MP3 + 合集 + 词表
   │     Package into MP3s, combined files and a word list
   ▼
out/release/
```

---

## 快速开始 / Quick start

需要 Python 3.9+ 和 `ffmpeg`。如果要从 PDF 提取，还需要 `poppler-utils` 和带中文语言包（chi_sim）的 `tesseract`。

Requires Python 3.9+ and `ffmpeg`. To extract from a PDF you also need `poppler-utils` and `tesseract` with the Chinese language pack (chi_sim).

```bash
pip install -r requirements.txt
bash scripts/download_models.sh     # 下载模型到 ./models（约 1 GB）/ download models into ./models (~1 GB)

# 用自带示例试一下 / Try the bundled example
python scripts/make_audio.py examples/words_sample.csv out/wav
python scripts/verify_asr.py out/wav/*.wav                     # 可选 / optional
python scripts/package.py examples/words_sample.csv out/wav out/release
```

### ① 准备单词表 / Prepare the word list

CSV 需要表头 `n,group,word,synonyms,meaning`，例子见 [`examples/words_sample.csv`](examples/words_sample.csv)：

The CSV needs the header `n,group,word,synonyms,meaning`. See [`examples/words_sample.csv`](examples/words_sample.csv):

```csv
n,group,word,synonyms,meaning
1,Day1,mitigate,"abate, alleviate",缓和，减轻
5,Day2,plausible,"credible, conceivable",1.可信的 2.看似合理的
```

- `group` 用来分文件夹和合集，比如按天；可以留空。
  `group` is used for folders and combined files (e.g. by day); it can be left empty.
- `synonyms` 可以留空，留空就不读 "Synonyms"。
  `synonyms` can be left empty; then "Synonyms" is not read.
- 中文里的 `…` 会读成「某事」（与…隔绝 → 与某事隔绝），`1.` `2.` 会读成「第一」「第二」。
  In the Chinese text, `…` is read as 「某事」 ("something"), and `1.` `2.` are read as 「第一」「第二」 ("first", "second").

如果单词表是 PDF，而且中文复制不出来，可以用 OCR 提取：

If your word list is a PDF whose Chinese text can't be copied, extract it with OCR:

```bash
python scripts/extract_pdf_table.py book.pdf words.csv --cols 0.153,0.329 0.335,0.66 0.665,0.853
```

`--cols` 是三列（单词、等价词、中文）在页面上的横向位置，用页面宽度的比例表示，需要按你的 PDF 调整。**OCR 一定会有错字，生成音频前请逐行校对。**

`--cols` gives the horizontal position of the three columns (word, synonyms, Chinese meaning) as fractions of the page width; adjust them for your PDF. **OCR always makes some mistakes, so proofread every row before generating audio.**

### ② 生成音频 / Generate audio

```bash
python scripts/make_audio.py words.csv out/wav            # 全部 / all words
python scripts/make_audio.py words.csv out/wav 1 200      # 只做第 1–200 个 / words 1–200 only
```

中断后重新运行会跳过已经生成的单词。在 2 核 CPU 上大约每个单词 4–5 秒，900 个词约 70 分钟。

If interrupted, re-running skips words that are already done. On a 2-core CPU it takes about 4–5 seconds per word, roughly 70 minutes for 900 words.

### ③ 抽查 / Spot-check

```bash
python scripts/verify_asr.py out/wav/0001.wav out/wav/0136.wav
```

会把每一段转写成文字，方便发现漏读或乱读。注意：语音识别本身对生僻英文单词经常拼错，所以它适合检查「有没有读、读没读乱」，判断不了发音准不准。最终还是要自己听。

This transcribes each spoken segment so you can catch missing or garbled parts. Note: the recognizer often misspells rare English words, so it tells you whether something was read and whether it came out garbled, not whether the pronunciation is correct. You still need to listen yourself.

### ④ 打包 / Package

```bash
python scripts/package.py words.csv out/wav out/release
```

---

## 踩过的坑（为什么这么设计）/ Lessons learned (why it works this way)

- **中英文用两个模型。** 试过的开源模型里，没有一个能用同一个声音把英文和中文都读好：中文好的读英文含糊，英文好的读中文很怪。所以英文用 Kokoro（af_heart），中文用 MeloTTS。
  **Two models, one per language.** None of the open-source models we tried could read both English and Chinese well in one voice: the good Chinese voices mumble English, and the good English voices sound odd in Chinese. So English uses Kokoro (af_heart) and Chinese uses MeloTTS.

- **编号用英文读，和单词连在一起。** MeloTTS 读「一」「二」「七」这种单个字几乎读不出来，所以编号交给英文声音，和单词一口气读完，中英切换也从四次减少到两次，衔接更顺。
  **The number is read in English, together with the word.** MeloTTS can barely say single characters like 「一」「二」「七」, so the English voice reads the number and the word in one go. This also cuts the switches between voices from four to two, so it flows better.

- **「意思是」引导再剪掉。** MeloTTS 单独读「缓和」「激增」这种两个字的词经常含糊。程序先让它读「意思是缓和」，再用语音识别的时间戳找到「意思是」结束的位置，把它剪掉，最后只留下「缓和」。没装语音识别模型时，会直接读中文意思。
  **A lead-in phrase that gets cut off.** MeloTTS often slurs short two-character words such as 「缓和」 when they're read alone. The script has it read 「意思是缓和」 ("meaning: 缓和"), uses the speech recognizer's timestamps to find where 「意思是」 ends, and cuts it off, leaving only 「缓和」. Without the recognition model installed, the meaning is read directly.

- **「等价词」换成英文 "Synonyms"。** MeloTTS 会把「等价词」读成类似「绑架词」的音。
  **"Synonyms" is said in English.** MeloTTS mispronounces 「等价词」 as something like 「绑架词」.

- **音量统一。** 每段都做了峰值归一化，避免中英文一大一小。
  **Even volume.** Every segment is peak-normalized so the two voices are equally loud.

想换声音：英文可以设置环境变量 `EN_SPEAKER`（Kokoro v1.0 的编号，3 = af_heart），中文模型在 `scripts/engines.py` 里替换。

To change voices: set the environment variable `EN_SPEAKER` for English (a Kokoro v1.0 speaker ID; 3 = af_heart). The Chinese model can be swapped in `scripts/engines.py`.

---

## 用到的开源项目 / Open-source projects used

- [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx)：离线推理框架 / offline inference framework（Apache-2.0）
- [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)：英文语音 / English voice（Apache-2.0）
- [MeloTTS](https://github.com/myshell-ai/MeloTTS)：中文语音 / Chinese voice（MIT）
- [SenseVoice](https://github.com/FunAudioLLM/SenseVoice)：语音识别，用于剪辑和抽查（可选）/ speech recognition for cutting and spot-checks (optional)

各模型的许可证以其原项目为准。

Each model's license is as stated by its original project.

---

## 关于词表版权 / About word-list copyright

本仓库只包含代码和一个自编的小示例，**不包含任何市售词汇书的内容**。

This repository contains only code and a small self-written example. **It does not include content from any commercial vocabulary book.**

本流程最初用《真经GRE等价词汇总》（[真经GRE · 张巍老师](http://www.grepass.vip/datashare)）测试，共 889 个词。该词表版权归原作者所有，本仓库不转载；如需使用，请从原作者渠道获取。

The workflow was first tested with 《真经GRE等价词汇总》 (the 真经GRE synonym list by [真经GRE · Mr. Zhang Wei](http://www.grepass.vip/datashare)), 889 words in total. That list is copyrighted by its author and is not redistributed here; please get it from the author's own channels if you want to use it.

用你自己的词表生成音频时，请注意原书的版权，生成的音频建议只做个人学习使用。

When generating audio from your own word list, please respect the original copyright; we recommend keeping the audio for personal study.

---

## License

代码使用 MIT License。/ The code is released under the MIT License.

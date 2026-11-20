# vocab-to-audio

把英语单词表（单词 + 等价词 + 中文意思）批量转成 MP3 音频，用来边听边背单词（GRE、托福、雅思都适用）。
全部在本地 CPU 上运行，不需要显卡，也不需要任何付费 API。

Turn an English vocabulary list (word, synonyms, Chinese meaning) into MP3 audio for listening practice. Runs offline on CPU with open-source models.

## 效果

每个单词读成一段，大约 5 秒：

> **"1. mitigate."**（英文女声）→ **"缓和"**（中文女声）→ **"Synonyms: abate, curtail, temper, ameliorate."**（英文女声）

输出三样东西：

| 文件 | 说明 |
|---|---|
| `per_word_mp3.zip` | 每个单词一个 MP3，按编号命名，按组（比如按天）分文件夹 |
| `<组名>_<起>-<止>.mp3` | 每组一个合集 MP3，单词之间停顿 1.2 秒，适合通勤从头听 |
| `word_list.xlsx` | 编号词表，每行对应的音频文件名 |

## 流程

```
PDF / Excel 单词表
   │  ① 整理成 CSV（可选：用 OCR 从 PDF 提取，然后人工校对）
   ▼
words.csv  (n, group, word, synonyms, meaning)
   │  ② 逐个生成音频（英文 Kokoro + 中文 MeloTTS）
   ▼
out/wav/0001.wav …
   │  ③ 抽查（可选：语音识别转写，检查有没有漏读、错读）
   │  ④ 打包成 MP3 + 合集 + 词表
   ▼
out/release/
```

## 快速开始

需要 Python 3.9+、`ffmpeg`；如果要从 PDF 提取，还需要 `poppler-utils` 和带中文语言包的 `tesseract`。

```bash
pip install -r requirements.txt
bash scripts/download_models.sh            # 下载模型到 ./models（约 1 GB）

# 用自带示例试一下
python scripts/make_audio.py examples/words_sample.csv out/wav
python scripts/verify_asr.py out/wav/*.wav           # 可选：抽查
python scripts/package.py examples/words_sample.csv out/wav out/release
```

### ① 准备单词表

CSV 需要表头 `n,group,word,synonyms,meaning`，例子见 [`examples/words_sample.csv`](examples/words_sample.csv)：

```csv
n,group,word,synonyms,meaning
1,Day1,mitigate,"abate, alleviate",缓和，减轻
5,Day2,plausible,"credible, conceivable",1.可信的 2.看似合理的
```

- `group` 用来分文件夹和合集，比如按天；可以留空。
- `synonyms` 可以留空，留空就不读 "Synonyms"。
- 中文里的 `…` 会读成「某事」（与…隔绝 → 与某事隔绝），`1.` `2.` 会读成「第一」「第二」。

如果单词表是 PDF，而且中文复制不出来，可以用 OCR 提取：

```bash
python scripts/extract_pdf_table.py book.pdf words.csv --cols 0.153,0.329 0.335,0.66 0.665,0.853
```

`--cols` 是三列（单词、等价词、中文）在页面上的横向位置，用页面宽度的比例表示，需要按你的 PDF 调整。**OCR 一定会有错字，生成音频前请逐行校对。**

### ② 生成音频

```bash
python scripts/make_audio.py words.csv out/wav            # 全部
python scripts/make_audio.py words.csv out/wav 1 200      # 只做第 1–200 个
```

中断后重新运行会跳过已经生成的单词。在 2 核 CPU 上大约每个单词 4–5 秒，900 个词约 70 分钟。

### ③ 抽查

```bash
python scripts/verify_asr.py out/wav/0001.wav out/wav/0136.wav
```

会把每一段转写成文字，方便发现漏读或乱读。注意：语音识别本身对生僻英文单词经常拼错，所以它适合检查「有没有读、读没读乱」，判断不了发音准不准。最终还是要自己听。

### ④ 打包

```bash
python scripts/package.py words.csv out/wav out/release
```

## 踩过的坑（为什么这么设计）

- **中英文用两个模型。** 试过的开源模型里，没有一个能用同一个声音把英文和中文都读好：中文好的读英文含糊，英文好的读中文很怪。所以英文用 Kokoro（af_heart），中文用 MeloTTS。
- **编号用英文读，和单词连在一起。** MeloTTS 读「一」「二」「七」这种单个字几乎读不出来，所以编号交给英文声音，和单词一口气读完，中英切换也从四次减少到两次，衔接更顺。
- **「意思是」引导再剪掉。** MeloTTS 单独读「缓和」「激增」这种两个字的词经常含糊。程序先让它读「意思是缓和」，再用语音识别的时间戳找到「意思是」结束的位置，把它剪掉，最后只留下「缓和」。没装语音识别模型时，会直接读中文意思。
- **「等价词」换成英文 "Synonyms"。** MeloTTS 会把「等价词」读成类似「绑架词」的音。
- **音量统一。** 每段都做了峰值归一化，避免中英文一大一小。

想换声音：英文可以设置环境变量 `EN_SPEAKER`（Kokoro v1.0 的编号，3 = af_heart），中文模型在 `scripts/engines.py` 里替换。

## 用到的开源项目

- [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx)：离线推理框架（Apache-2.0）
- [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)：英文语音（Apache-2.0）
- [MeloTTS](https://github.com/myshell-ai/MeloTTS)：中文语音（MIT）
- [SenseVoice](https://github.com/FunAudioLLM/SenseVoice)：语音识别，用于剪辑和抽查（可选）

各模型的许可证以其原项目为准。

## 关于词表版权

本仓库只包含代码和一个自编的小示例，**不包含任何市售词汇书的内容**。

本流程最初用《真经GRE等价词汇总》（[真经GRE · 张巍老师](http://www.grepass.vip/datashare)）测试，共 889 个词。该词表版权归原作者所有，本仓库不转载；如需使用，请从原作者渠道获取。用你自己的词表生成音频时，请注意原书的版权，生成的音频建议只做个人学习使用。

## License

代码使用 MIT License。

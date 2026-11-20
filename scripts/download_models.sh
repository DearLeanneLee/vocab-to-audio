#!/usr/bin/env bash
# 下载本项目用到的语音合成 / 语音识别模型到 ./models
# Download the TTS / ASR models used by this project into ./models
set -euo pipefail
mkdir -p models && cd models
BASE=https://github.com/k2-fsa/sherpa-onnx/releases/download
get() { [ -d "$2" ] || { echo "Downloading $2 ..."; curl -sSL "$BASE/$1/$2.tar.bz2" | tar xj; }; }
get tts-models kokoro-multi-lang-v1_0          # 英文声音 / English voice (af_heart)
get tts-models vits-melo-tts-zh_en             # 中文声音 / Chinese voice (MeloTTS)
if [ "${WITH_ASR:-1}" = "1" ]; then
  get asr-models sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2025-09-09   # 可选：抽查和剪辑 / optional: spot-checks and cutting
fi
echo "完成 / Done."

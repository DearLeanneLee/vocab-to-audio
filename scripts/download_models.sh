#!/usr/bin/env bash
# Download the TTS / ASR models used by this project into ./models
set -euo pipefail
mkdir -p models && cd models
BASE=https://github.com/k2-fsa/sherpa-onnx/releases/download
get() { [ -d "$2" ] || { echo "Downloading $2 ..."; curl -sSL "$BASE/$1/$2.tar.bz2" | tar xj; }; }
get tts-models kokoro-multi-lang-v1_0          # English voice (af_heart)
get tts-models vits-melo-tts-zh_en             # Chinese voice (MeloTTS)
if [ "${WITH_ASR:-1}" = "1" ]; then
  get asr-models sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2025-09-09   # optional: spot-check output
fi
echo "Done."

# STT (Speech-to-Text) Setup — japanese-tutor Profile

## Initial Installation

The profile had `stt.enabled: true` and `stt.provider: local` set in config.yaml, but `faster-whisper` was not installed:

```bash
python3 -m pip install faster-whisper
```

This installs the following key dependencies:
- `faster-whisper` (CTranslate2-optimized Whisper)
- `ctranslate2` (inference engine)
- `huggingface-hub` (model download)
- `onnxruntime` (CPU backend)

## Model Download

On first run, faster-whisper downloads the model (~1.4GB for `base`) to `~/.cache/huggingface/hub/`. Internet connection required.

## Config (as set)

```yaml
stt:
  enabled: true
  provider: local
  local:
    model: base
    language: ''  # auto-detect
```

The empty `language` field means auto-detect — important for mixed Russian/Japanese voice messages.

## Model Size Guide

| Model  | Size   | Accuracy | Speed       |
|--------|--------|----------|-------------|
| tiny   | ~150MB | Lowest   | Fastest     |
| base   | ~300MB | Good     | Fast        |
| small  | ~750MB | Better   | Moderate    |
| medium | ~1.5GB | High     | Slow        |
| large-v3| ~3GB  | Best     | Slowest     |

`base` is a good default for Russian + Japanese voice messages.

## Verification

Send a voice message in Telegram. The gateway auto-transcribes it via STT and passes the text to the agent. No restart needed after installation if the gateway was already stopped — start fresh.

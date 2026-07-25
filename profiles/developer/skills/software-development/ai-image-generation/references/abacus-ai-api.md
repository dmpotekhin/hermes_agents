# Abacus AI RouteLLM — Image Generation API

## Endpoint

```
POST https://routellm.abacus.ai/v1/chat/completions
Content-Type: application/json
Authorization: Bearer <api_key>
```

## Request format

```json
{
  "model": "flux2_pro",
  "modalities": ["image", "text"],
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "A sunset over Paris with Eiffel Tower"}
      ]
    }
  ],
  "image_config": {
    "aspect_ratio": "square_hd"
  }
}
```

Optional `image_config` fields:
- `num_images` (1-4, model-dependent)
- `quality` ("low", "medium", "high" — OpenAI models only)
- `resolution` ("1080p", "2K", "4K" — nano_banana_pro only)
- `rewrite_prompt` (bool, default true — improves prompt quality)

Reference images (image-to-image): add `{"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}` to content array. Max 3.

## Response format

```json
{
  "choices": [
    {
      "message": {
        "images": [
          {
            "image_url": {
              "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgA..."
            }
          }
        ],
        "content": ""
      }
    }
  ]
}
```

Image is always a **data URI** (`data:image/<fmt>;base64,...`).

## Fallback extraction paths

If `images` array is empty or missing, check:
1. `choices[0].message.content` — search for `data:image` strings via regex
2. `choices[0].message.inline_data.data` — raw base64 string

## Available models

| Model ID            | Display          | Aspect ratio format               | Strengths                         |
|---------------------|------------------|-----------------------------------|-----------------------------------|
| `flux2_pro`         | FLUX 2 Pro       | `square_hd/landscape_16_9/portrait_16_9` | High quality, photorealistic (default) |
| `flux_pro_ultra`    | FLUX Pro Ultra   | `1:1/16:9/9:16`                   | Highest quality, photorealistic   |
| `flux2`             | FLUX 2           | `square_hd/landscape_16_9/portrait_16_9` | Fast, good quality                |
| `nano_banana_pro`   | Nano Banana Pro  | `square_hd/landscape_16_9/portrait_16_9` | Up to 4K resolution, DeepMind     |
| `midjourney`        | MidJourney       | `1:1/16:9/9:16`                   | Artistic, stylistic               |
| `dalle`             | DALL-E           | `1:1/16:9/9:16`                   | Creative, strong prompt adherence |
| `seedream`          | Seedream         | `1:1/16:9/9:16`                   | —                                 |

## Aspect ratio mapping

FLUX family (flux2, flux2_pro, nano_banana_pro):
- `square` → `square_hd`
- `landscape` → `landscape_16_9`
- `portrait` → `portrait_16_9`

Standard models (midjourney, dalle, flux_pro_ultra, seedream):
- `square` → `1:1`
- `landscape` → `16:9`
- `portrait` → `9:16`

## Credentials

Resolution order:
1. `ABACUS_AI_API_KEY` env var + `ABACUS_AI_BASE_URL` env var (falls back to routellm.abacus.ai)
2. `custom_providers` section in Hermes `config.yaml` (entry with `name: abacus-ai`)

For project-level use: put `ABACUS_AI_API_KEY=s2_...` in `backend/.env`.

## Python response parser

```python
import base64
import re
from typing import Optional


def extract_image_from_abacus_response(data: dict) -> Optional[bytes]:
    """Extract decoded image bytes from Abacus AI chat/completions response."""
    choices = data.get("choices", [])
    if not choices:
        return None

    msg = choices[0].get("message", {})
    images = msg.get("images") or []

    for img in images:
        url = (img.get("image_url") or {}).get("url") or img.get("url", "")
        if url.startswith("data:image"):
            match = re.search(r"base64,([a-zA-Z0-9+/=]+)", url)
            if match:
                return base64.b64decode(match.group(1))

    # Fallback: inline data in content
    content = msg.get("content", "")
    if "data:image" in content:
        match = re.search(r"data:image/[^;]+;base64,([a-zA-Z0-9+/=]+)", content)
        if match:
            return base64.b64decode(match.group(1))

    # Fallback: inline_data field
    inline = msg.get("inline_data") or msg.get("inlineData")
    if isinstance(inline, dict) and inline.get("data"):
        return base64.b64decode(inline["data"])

    return None
```

## Timeout

300 seconds. Image generation can take 30-120 seconds depending on model and load.

## Notes

- API is OpenAI-compatible in structure but NOT in semantics. Uses `modalities` and `image_config` instead of OpenAI's image generation params. Do not use OpenAI Python SDK for this.
- `num_images` > 1 may work but many models only return one image.
- Reference images are passed as content parts, not as a separate parameter.
- The Hermes `image_gen/abacus_ai` plugin at `~/.hermes/plugins/image_gen/abacus_ai/` is the authoritative source for the latest API format.

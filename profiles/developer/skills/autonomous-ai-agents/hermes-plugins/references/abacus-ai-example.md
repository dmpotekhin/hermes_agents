# Abacus AI Image Gen Plugin — Full Install Example

Example of installing the Abacus AI image generation plugin for Hermes Agent.

Source: https://github.com/ZoniBoy00/hermes-agent-abacus-ai

## Step-by-step

### 1. Clone

```bash
git clone https://github.com/ZoniBoy00/hermes-agent-abacus-ai /tmp/hermes-agent-abacus-ai
```

### 2. Inspect structure

```bash
ls /tmp/hermes-agent-abacus-ai/abacus_ai/
# __init__.py  plugin.yaml  provider.py  config.py  models.py  utils.py  background.py
```

`plugin.yaml` declares `kind: backend` and `requires_env: ABACUS_AI_API_KEY`.

### 3. Copy to plugins directory

```bash
mkdir -p ~/.hermes/plugins/image_gen
cp -r /tmp/hermes-agent-abacus-ai/abacus_ai ~/.hermes/plugins/image_gen/abacus_ai/
```

### 4. Configure via hermes config set

```bash
# Enable the plugin
hermes config set plugins.enabled '["image_gen/abacus_ai"]'

# Set image_gen provider
hermes config set image_gen.provider abacus_ai

# Configure API credentials (REPLACE with actual key)
hermes config set custom_providers '[{"name": "abacus-ai", "api_key": "s2_YOUR_KEY", "base_url": "https://routellm.abacus.ai/v1"}]'
```

### 5. Restart

```bash
hermes gateway restart
```

### 6. Verify

```bash
hermes plugins list
```

## Plugin config resolution

The plugin (`abacus_ai/config.py`) resolves credentials in this order:
1. `custom_providers` in `config.yaml` (entry with `name: "abacus-ai"`)
2. `ABACUS_AI_API_KEY` / `ABACUS_AI_BASE_URL` environment variables

Model resolution order (`resolve_model_chain`):
1. Explicit model passed at call time
2. `ABACUS_AI_IMAGE_MODEL` env var
3. `image_gen.abacus_ai.model` in config.yaml
4. `image_gen.model` in config.yaml
5. Default: `flux2_pro`

## Optional cleanup

```bash
rm -rf /tmp/hermes-agent-abacus-ai
```

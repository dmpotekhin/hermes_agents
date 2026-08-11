# Provider Switch Mid-Project — Recipe

What to do when user switches LLM/embedding provider after the plan is written and subagents are already running.

## Scenario (from RAG Assistant session)

Plan specified:
- LLM: Ollama `llama3.2:3b`
- Embeddings: Ollama `nomic-embed-text`

Mid-execution user says:
- "Use DeepSeek API instead, I have a token"
- "I don't have Ollama installed"

## Step-by-step

### 1. Update spec and plan IMMEDIATELY

```bash
# Update config.yaml in spec
patch spec.md old_llm_config new_llm_config
patch plan.md old_llm_config new_llm_config
git add -A && git commit -m "plan: switch to DeepSeek API, env var for key"
```

### 2. Add API key handling

- Config key in `config.yaml` → `# api_key is read from DEEPSEEK_API_KEY env var`
- Add `get_api_key()` function to `config.py` reading `os.environ["DEEPSEEK_API_KEY"]`
- Add `.env` to `.gitignore`
- Never hardcode keys, never commit them

### 3. Regenerate task briefs

If subagents are still running with old briefs, the task they're working on will create wrong config. Options:

A) **Let current task finish, fix in review** — works for small tasks (1-2 files)
B) **Add context to fix dispatcher** — dispatch a fix subagent after current task completes
C) **Kill and restart** — for critical config tasks (Task 1 scaffolding)

### 4. Update global constraints for reviewers

When dispatching reviewers, include the NEW provider constraints explicitly:

```
Global constraints:
- LLM provider MUST be "deepseek", model "deepseek-flash", endpoint "https://api.deepseek.com/v1"
- Embedding: "sentence-transformers", "all-MiniLM-L6-v2"
- API key from DEEPSEEK_API_KEY env var (NOT hardcoded)
```

Reviewers will correctly flag brief-vs-constraint conflicts as Critical.

### 5. Fix subagent tests for new provider

Tests that call real APIs (e.g., `test_commands.py` with DeepSeek) need the API key in env. The `execute_code` pattern:

```python
import subprocess, os

# Find key in Hermes profile .env
venv = "/Users/.../project/.venv/bin/python"
key_file = os.path.expanduser("~/.hermes/profiles/developer/.env")
with open(key_file) as f:
    for line in f:
        if line.startswith("DEEPSEEK_API_KEY="):
            key = line.split("=", 1)[1].strip().strip('"').strip("'")
            break

env = dict(os.environ)
env["DEEPSEEK_API_KEY"] = key
r = subprocess.run([venv, "-m", "pytest", "tests/test_commands.py", "-v"],
                   capture_output=True, text=True, cwd=project_root, env=env)
```

### 6. Dual-provider pattern (LLM ≠ Embeddings)

When LLM uses API but embeddings use local model:

```yaml
llm:
  provider: "deepseek"           # API
  model: "deepseek-flash"
  endpoint: "https://api.deepseek.com/v1"

embedding:
  provider: "sentence-transformers"  # local
  model: "all-MiniLM-L6-v2"
  endpoint: ""
```

Keep them in separate config sections so each can be swapped independently.

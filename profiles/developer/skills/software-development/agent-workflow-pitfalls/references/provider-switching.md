# Provider Switching Checklist (LLM / Embeddings)

When the user signals a provider change mid-project, follow this order.
Pattern from RAG Assistant session: switched LLM (Ollama→DeepSeek) and
embedding backend (Ollama→sentence-transformers) during active SDD execution.

## P0: STOP dispatching new tasks

When the user says "use X instead of Y", do NOT dispatch the next
implementer. Update everything first.

## LLM Provider Switch

1. **Update config.yaml** — model, endpoint, provider fields
2. **Add API key pattern** — `get_api_key()` in config.py from env var.
   API key NEVER in config.yaml — git history is forever.
3. **Add .env to .gitignore** — prevents accidental commits
4. **Update commands.py** — client constructor uses `api_key=get_api_key()`
5. **Update ALL test fixtures** — search old provider strings:
   ```bash
   grep -rn "ollama\|llama3.2\|nomic" tests/
   ```
   Test config values MUST match config.yaml — reviewers flag mismatches
   as Critical.
6. **Regenerate task briefs** — `task-brief PLAN N` for all pending tasks.
   Implementers get stale Ollama code in old briefs otherwise.

## Embedding Provider Switch (Ollama → sentence-transformers)

1. **Update config.yaml** — embedding section
2. **Replace embedding wrapper** — HTTP client class → `SentenceTransformer(model)`
3. **Check ChromaDB compat** — embedding callable MUST be class with
   `__call__(self, input)` — param name `input` is enforced by ChromaDB 0.5.x
4. **Pin numpy** — `numpy==1.26.4`. Torch 2.2.x crashes with numpy≥2.0.
5. **Update requirements.txt** — add `sentence-transformers`, keep `openai`
6. **Verify model cache** — check `~/.cache/huggingface/hub/` for
   `models--sentence-transformers--all-MiniLM-L6-v2`
7. **Update ALL test config fixtures** — using `replace_all`:
   ```
   embedding_provider="ollama", embedding_model="nomic-embed-text"
   → embedding_provider="sentence-transformers", embedding_model="all-MiniLM-L6-v2"
   ```
8. **Update test config endpoint** — `endpoint="http://localhost:11434/v1"`
   → `endpoint=""`

## Common Mistakes

- **Forgetting test fixtures**: plan code has old values → reviewer flags
  implementer → implementer followed the brief faithfully → wasted loop
- **Not regenerating task briefs**: implementers get Ollama code
- **Mixing providers**: some tests use old config, some new

## Real Session Log

Trigger: User mid-session "так можно deepseek использовать"

Actions:
1. Updated plan config: ollama→deepseek, ollama→sentence-transformers
2. `replace_all` for embedding_provider in plan (3 occurrences)
3. `replace_all` for llm_provider in plan
4. Fix subagent for Task 1: DeepSeek config + get_api_key()
5. Fix subagent for Task 2: sentence-transformers embedding wrapper
6. Tests caught numpy≥2.0 incompatibility → pinned numpy==1.26.4

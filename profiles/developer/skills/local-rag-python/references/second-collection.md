# Adding a Second ChromaDB Collection

Pattern for extending a RAG app with a new entity type stored in its own ChromaDB collection.

## When to Use

When the existing app stores links in a `"links"` collection and you need to add
a semantically different entity (prompts, notes, documents) — use a separate
collection, not type-tagging the existing one.

## Pattern

```python
class PromptDB:
    """Second collection — mirrors LinkDB pattern, independent embedding space."""

    def __init__(self, config: Config):
        self.client = chromadb.PersistentClient(path=config.chroma_path)
        self.embedding_fn = self._make_embedding_fn(config)
        self.collection = self.client.get_or_create_collection(
            name="prompts",                   # different collection name
            embedding_function=self.embedding_fn,  # same embedding model
        )

    def _make_embedding_fn(self, config: Config):
        # Identical to LinkDB — reuse, don't duplicate if possible
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(config.embedding_model)
        class SentenceTransformersEmbedding:
            def __call__(self, input):
                return model.encode(input).tolist()
        return SentenceTransformersEmbedding()

    def add_prompt(self, text, description, tags=None):
        pid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        tag_str = ",".join(tags) if tags else ""
        self.collection.add(
            ids=[pid],
            documents=[text],         # what gets embedded
            metadatas=[{              # what gets returned
                "text": text,
                "description": description,
                "tags": tag_str,
                "created_at": now,
            }],
        )
        return pid

    def search(self, query, n_results=5):
        results = self.collection.query(query_texts=[query], n_results=n_results)
        return self._format_results(results)

    def list_prompts(self):
        results = self.collection.get()
        return self._format_get(results)

    def delete_prompt(self, id):
        existing = self.collection.get(ids=[id])
        if not existing["ids"]:
            return False
        self.collection.delete(ids=[id])
        return True

    def _make_item(self, pid, meta):
        # Convert stored format to API format
        tags_str = meta.get("tags", "")
        return {
            "id": pid,
            "text": meta.get("text", ""),
            "description": meta.get("description", ""),
            "tags": [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else [],
            "created_at": meta.get("created_at", ""),
        }
```

## Key Decisions

- **Separate collection, same DB**: `PersistentClient` handles multiple collections in one `chroma.sqlite3`
- **Same embedding model**: One `SentenceTransformer` instance per DB class, lazy-loaded
- **Tags as comma-separated string**: ChromaDB metadata only supports `str | int | float | bool` — no lists
- **No duplicate detection**: Unlike links (URL uniqueness), prompts are intentionally duplicable
- **_make_item for format conversion**: Internal storage format ≠ API response format; convert at the boundary

## Lazy Init in FastAPI

Same pattern as the primary DB — avoid loading models at import time:

```python
_prompt_db = None

def _get_prompt_db():
    global _prompt_db
    if _prompt_db is None:
        from db import PromptDB
        _prompt_db = PromptDB(config)
    return _prompt_db
```

## Testing

Isolated ChromaDB path per test module, cleaned up in fixture teardown:

```python
TEST_CHROMA = "./test_prompts_db"

@pytest.fixture
def prompt_db():
    if os.path.exists(TEST_CHROMA):
        shutil.rmtree(TEST_CHROMA)
    config = Config(..., chroma_path=TEST_CHROMA, ...)
    db = PromptDB(config)
    yield db
    shutil.rmtree(TEST_CHROMA, ignore_errors=True)
```

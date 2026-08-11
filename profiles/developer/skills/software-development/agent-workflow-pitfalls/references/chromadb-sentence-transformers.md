# ChromaDB + sentence-transformers Integration

Working pattern for local RAG with ChromaDB and sentence-transformers
(no Ollama, no external embedding server).

## Embedding Function — MUST be a class

ChromaDB 0.5.x inspects `__call__(self, input)` signature.
A plain function is silently accepted at init but fails at query.

```python
from sentence_transformers import SentenceTransformer

class SentenceTransformersEmbedding:
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def __call__(self, input: list[str]) -> list[list[float]]:
        return self.model.encode(input).tolist()
```

## Complete LinkDB init

```python
import chromadb
from config import Config

class LinkDB:
    def __init__(self, config: Config):
        self.client = chromadb.PersistentClient(path=config.chroma_path)
        self.embedding_fn = SentenceTransformersEmbedding(config.embedding_model)
        self.collection = self.client.get_or_create_collection(
            name="links",
            embedding_function=self.embedding_fn,
        )
```

## config.yaml

```yaml
embedding:
  provider: "sentence-transformers"
  model: "all-MiniLM-L6-v2"
  endpoint: ""  # not used for local models
```

## requirements.txt

```
sentence-transformers==3.3.1
numpy==1.26.4        # torch 2.2.x is incompatible with numpy 2.x
chromadb==0.5.23
```

## Model caching

First run downloads ~90MB to `~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/`.
Subsequent runs are ~1s. In test fixtures, prefer models already in cache.
Check cache: `ls ~/.cache/huggingface/hub/models--*/`

## Test fixture

```python
import shutil, os, pytest

TEST_CHROMA = "./test_chroma_db"

@pytest.fixture
def link_db():
    if os.path.exists(TEST_CHROMA):
        shutil.rmtree(TEST_CHROMA)
    config = Config(
        chroma_path=TEST_CHROMA,
        embedding_model="all-MiniLM-L6-v2",
        # ... other config fields
    )
    db = LinkDB(config)
    yield db
    shutil.rmtree(TEST_CHROMA, ignore_errors=True)
```

## chromadb metadata constraints

- `None` values in metadata are rejected → use empty string `""` instead
- Normalize `or None` on read: `meta.get("folder") or None`
- Parameter name for embedding `__call__` must be `input` (not `texts`)

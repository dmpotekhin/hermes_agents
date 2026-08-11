# ChromaDB adapter brief — reference-code bugs + offline-embedding verification

Task: implement a `LinkDB` (chromadb 0.5.23 PersistentClient) from a brief that supplied
exact reference code. The brief's code was a design guide, not copy-paste — three real
integration bugs surfaced only by running it against the actual installed chromadb.

## Bug 1 — embedding function `__call__` param MUST be named `input`

chromadb validates the custom embedding function's signature against its protocol:

```python
function_signature = signature(embedding_function.__class__.__call__).parameters.keys()
protocol_signature   = signature(EmbeddingFunction.__call__).parameters.keys()
if not function_signature == protocol_signature:
    raise ValueError("Expected EmbeddingFunction.__call__ to have the following signature: ...")
```

The protocol param is `input`, so a wrapper like `def __call__(self, texts)` fails at
`get_or_create_collection(...)` with `ValueError: Expected ... got odict_keys(['self', 'texts'])`,
BEFORE any query/add. Fix: name the parameter `input` (override the builtin deliberately):

```python
def __call__(self, input):
    resp = httpx.post(f"{endpoint}/embeddings",
                      json={"model": model, "input": input}, timeout=30)
```

Note: chromadb ≤0.4.16 accepted `texts`; the `input` rename is the post-0.4.16 interface.
Map the custom fn to a `class` with `__call__` — the `EmbeddingFunction` protocol is duck-typed
by parameter NAMES, not types.

## Bug 2 — chromadb metadata rejects `None` values

chromadb metadata values must be `str | int | float | bool`; `None` raises:

```
ValueError: Expected metadata value to be a str, int, float or bool, got None which is a NoneType in add.
```

A brief storing `"last_opened": None` (and reading it back as-is) breaks every `add`/`update`.
Store a `""` sentinel and normalize `or None` on read:

```python
metadatas=[{..., "last_opened": ""}]          # store ""
# read back:
"last_opened": meta.get("last_opened") or None   # normalize "" -> None
```

## Bug 3 — PersistentCollection test-fixture race → "attempt to write a readonly database"

A fixture that reuses ONE persistent dir removed on teardown (e.g. `shutil.rmtree("./test_chroma_db")`)
fails non-deterministically when tests run back-to-back: chromadb's PersistentClient keeps SQLite
handles alive, so deleting the dir out from under the still-open client corrupts the next test's
fresh open → `sqlite3.OperationalError: attempt to write a readonly database`.
The SAME test passes in isolation (`pytest tests/x.py::single_test`) but 1 passes / 4 fail in sequence
(whatever you run first this launch passes, the rest fail). Fix: give each test its own subdir:

```python
path = os.path.join(TEST_CHROMA, uuid.uuid4().hex)
db = LinkDB(Config(..., chroma_path=path, ...))
yield db
shutil.rmtree(TEST_CHROMA, ignore_errors=True)   # clean base dir after each test
```

Symptom signature to recognize: `sqlite3.OperationalError` only when tests are NOT isolated;
isolated single test passes. This is a fixture design bug, not an adapter bug.

## Bug 4 — a plain function is rejected even with the param named `input`

Sharper variant of Bug 1. A brief may correctly name its param `input` yet still supply a
**plain function** (not a callable class):

```python
def _make_embedding_fn(self, config: Config):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(config.embedding_model)
    def embed(input):
        return model.encode(input).tolist()
    return embed
```

This FAILS chromadb's check identically — `get_or_create_collection` inspects
`embedding_function.__class__.__call__`, and on a plain function that attribute reflects as the
built-in `(*args, **kwargs)`, so the comparison yields
`Expected ... odict_keys(['self', 'input']), got odict_keys(['self', 'args', 'kwargs'])`.
The param name is irrelevant; chromadb needs a **callable instance** whose class defines
`def __call__(self, input)`. Wrap the same encode logic in a class:

```python
def _make_embedding_fn(self, config: Config):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(config.embedding_model)

    class SentenceTransformersEmbedding:
        def __call__(self, input):
            return model.encode(input).tolist()

    return SentenceTransformersEmbedding()
```

Keeps the brief's exact `model.encode(input).tolist()` logic; only adds the wrapper class chromadb
requires. Also satisfies the signature check that the fresh-install `sentence-transformers.path`
needs — the encode call shape stays identical.

## Bug 5 — sentence-transformers install pulls numpy 2.x that crashes torch 2.2.x

Installing `sentence-transformers==3.3.1` resolves numpy to the latest (2.4.x), and pins/builds
torch 2.2.x. torch 2.2.x cannot interoperate with numpy 2 — `model.encode()` fails at runtime with
`RuntimeError: Numpy is not available` (and a `UserWarning: Failed to initialize NumPy:
_ARRAY_API not found` at torch import). In code this surfaces late, not at import:
`from sentence_transformers import SentenceTransformer` succeeds, then `encode()` raises.

Fix: pin `numpy==1.26.4` (or any numpy <2) for torch 2.2.x. Durable and cheap:

```bash
pip install "numpy==1.26.4"
```

Check numpy compatibility against EVERY pinned dependency before pinning: `numpy>=1.17`
(transformers), `numpy>=1.26.4,<2.7` (scipy 1.x), `numpy>=1.24.1` (scikit-learn),
`numpy>=1.22.5` (chromadb) — all satisfied by 1.26.4.

Related benign warning: sentence-transformers pulls `tokenizers 0.22.2` while chromadb 0.5.23 pins
`<=0.20.3`. This is only a pip resolver warning — chromadb still imports and runs fine (the pin is
not enforced at import). Leave it, or note it in the report; don't force a downgrade that breaks
transformers.

## Offline-model verification: use an already-cached model, don't stall on a blocked download

`SentenceTransformer("all-MiniLM-L6-v2")` auto-downloads ~90MB from HuggingFace on first use.
If that download is user-denied or stalls (watch for a pit-stall: only small config blobs land in
`~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/` and the `*.incomplete`
weight blob stays 0 bytes), do NOT retry the download. Verify the integration with a model already
in the local HF cache instead (`~/.cache/huggingface/hub/models--<org>--<name>/`). The code path
is identical regardless of which sentence-transformers model loads; the config/fixture model name
only affects which weights are loaded.

```python
# check what's cached before deciding the test-fixture model name
import os; hub = os.path.expanduser("~/.cache/huggingface/hub"); os.listdir(hub)
```

If you point the test fixture at a cached model to get a green run, note explicitly in your report
that this differs from the production config model (which needs its own one-time download).

## Environment caveat: embedding provider down → tests fail on ConnectError

Every add/search embeds via HTTP to the provider endpoint. If Ollama (or whatever) isn't running,
all embedding tests fail identically on `httpx.ConnectError: [Errno 61] Connection refused in add.`
That's the EXPECTED environmental blocker, distinct from real adapter bugs. Don't chase it as a code
bug — but DO get real green evidence another way (below).

## Offline-verification pattern: mock the embedding server to prove adapter logic

To exercise the real adapter code end-to-end when the real embedding provider is down, stand up a
throwaway HTTP server that speaks the OpenAI-compatible embeddings shape the adapter consumes
(`POST {endpoint}/embeddings` → `{data: [{embedding: [...]}]}`, accepting either a single string or
a list for `input`). Point the test `Config` at it, run the UNMODIFIED test files. See
`scripts/mock_embeddings_server.py` for a ready-to-run version (port via argv).

- Deterministic pseudo-embeddings (sha256 bytes → floats) are fine for structural tests.
- Start it as a **tracked background process** (`background=true`), health-check with curl, run
  pytest, then kill it and `rm` the script. Never smuggle `&` into a foreground command.
- This is genuine verification (real `db.py` code paths), not fabricated output — the mock only
  stands in for the unavailable network service.

## Takeaway

The full workflow matched `spec-driven-implementation`: wrote the brief's tests first (failed at
import — valid TDD), then implemented, then ran — and the bugs above (all framework-version
contracts the brief's code violated, invisible to static reading) surfaced only at runtime. Verify
dependency contracts against the ACTUAL installed version, not the brief's assumed version. Two
embedding-provider migrations (Ollama → sentence-transformers) taught the same lesson twice: the
brief's literal example code is a design guide, and the runtime contract (param name AND callable
class shape) must be confirmed by actually running it.

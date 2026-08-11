# Why ChromaDB Embedding Function Must Use `input` Not `texts`

## The Error

When passing a plain function as ChromaDB's embedding function:

```python
def embed(texts):
    return model.encode(texts).tolist()

collection = client.create_collection("x", embedding_function=embed)
```

ChromaDB 0.5.x raises:

```
TypeError: embed() got an unexpected keyword argument 'input'
```

## Root Cause

ChromaDB internally calls the embedding function with `input=` as a keyword argument:

```python
# Inside ChromaDB source (simplified):
result = self._embedding_function(input=documents)
```

If your function uses `texts` as the parameter name, Python raises TypeError because the keyword name doesn't match.

## The Fix

Use a class with `__call__` that accepts `input`:

```python
class EmbeddingFn:
    def __init__(self, model):
        self.model = model
    def __call__(self, input):
        return self.model.encode(input).tolist()
```

Or use a lambda wrapper:

```python
embedding_fn = lambda input: model.encode(input).tolist()
```

Both work because the parameter is named `input`, matching what ChromaDB passes.

## Version Note

This behavior was observed on chromadb 0.5.23. Earlier versions may accept any parameter name, but 0.5.x is strict.

"""Throwaway mock OpenAI-compatible /v1/embeddings server.

Purpose: verify adapter code end-to-end when the real embedding provider
(e.g. Ollama) is down or not installed. Speaks exactly the shape `db` adapters
consume: POST {endpoint}/embeddings  ->  {"data": [{"index": i, "embedding": [...]}]}
Accepts `input` as either a single string or a list of strings.

Usage:
    python mock_embeddings_server.py [port]     # default 9777
Then point the adapter's Config at http://127.0.0.1:<port>/v1 and run your unmodified
tests. Start it as a TRACKED background process; on completion kill it.

Embeddings are deterministic pseudo-vectors (sha256 of the text) — fine for
structural tests (add/search/list/update), not for real semantic ranking.
"""
import json
import sys
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer

DIM = 768


def embed(text: str):
    h = hashlib.sha256(text.encode()).digest()
    return [int(b) - 128 for b in h] + [0.0] * (DIM - len(h))


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/v1/embeddings":
            return self._send(404, {"error": "not found"})
        length = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(length) or b"{}")
        inputs = data.get("input", [])
        if isinstance(inputs, str):
            inputs = [inputs]
        out = [{"index": i, "embedding": embed(t)} for i, t in enumerate(inputs)]
        self._send(200, {"data": out, "model": data.get("model")})

    def log_message(self, *a):  # silence request logging
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9777
    print(f"mock embeddings on :{port}", flush=True)
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()

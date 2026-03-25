import json
import math
import urllib.request

_OLLAMA_URL = "http://localhost:11434/api/embeddings"
_EMBED_MODEL = "nomic-embed-text"
_SIMILARITY_THRESHOLD = 0.85


def get_embedding(text: str) -> list[float] | None:
    """Fetch embedding vector from ollama for the given text."""
    payload = json.dumps({"model": _EMBED_MODEL, "prompt": text}).encode()
    try:
        req = urllib.request.Request(
            _OLLAMA_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())["embedding"]
    except Exception:
        return None


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def load_merchant_embeddings(conn) -> list[tuple[str, str, list[float]]]:
    """Load all merchant_map rows that have a stored embedding."""
    rows = conn.execute(
        "SELECT name, category, embedding FROM merchant_map WHERE embedding IS NOT NULL"
    ).fetchall()
    result = []
    for name, category, emb_json in rows:
        try:
            result.append((name, category, json.loads(emb_json)))
        except (json.JSONDecodeError, TypeError):
            continue
    return result


def find_similar_merchant(
    cleaned_name: str,
    merchant_embeddings: list[tuple[str, str, list[float]]],
) -> tuple[str, str, float] | None:
    """
    Compare cleaned_name against stored embeddings.
    Returns (matched_name, category, score) if above threshold, else None.
    """
    if not merchant_embeddings:
        return None

    query_vec = get_embedding(cleaned_name)
    if query_vec is None:
        return None

    best_score = 0.0
    best_match = None
    for name, category, stored_vec in merchant_embeddings:
        score = cosine_similarity(query_vec, stored_vec)
        if score > best_score:
            best_score = score
            best_match = (name, category, score)

    if best_match and best_score >= _SIMILARITY_THRESHOLD:
        return best_match
    return None


def store_embedding(conn, name: str, embedding: list[float]):
    """Persist an embedding for a merchant_map entry."""
    conn.execute(
        "UPDATE merchant_map SET embedding = ? WHERE name = ?",
        (json.dumps(embedding), name),
    )

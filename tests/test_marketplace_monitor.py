import io
import json

from src.marketplace_monitor import compare, embed_text, snapshot


def test_changed_listing_requires_review_and_preserves_seller():
    before = snapshot("seller-42", "Camera", "<h1>Camera</h1><p>in stock</p>")
    after = snapshot("seller-42", "Camera", "<h1>Camera</h1><p>sold out</p>")

    handoff = compare(before, after)

    assert handoff.changed is True
    assert handoff.order_state == "review_required"
    assert handoff.seller == "seller-42"


def test_same_listing_keeps_watching():
    current = snapshot("seller-42", "Camera", "<p>in stock</p>")
    handoff = compare(current, current)
    assert handoff.changed is False
    assert handoff.order_state == "watching"


def test_embed_text_accepts_openai_compatible_response(monkeypatch):
    response = {
        "object": "list",
        "data": [{"object": "embedding", "embedding": [0.1, 0.2], "index": 0}],
        "model": "text-embedding-3-small",
        "usage": {"prompt_tokens": 1, "total_tokens": 1},
    }

    class FakeResponse(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

    monkeypatch.setenv("INFRAI_API_KEY", "test-key")
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda request, timeout: FakeResponse(json.dumps(response).encode()),
    )

    assert embed_text("camera listing") == response

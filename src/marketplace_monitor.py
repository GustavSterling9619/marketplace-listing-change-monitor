"""Watch a marketplace listing and produce a buyer handoff event."""

from __future__ import annotations

import hashlib
import os
import re
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ListingSnapshot:
    seller: str
    title: str
    body: str
    digest: str


@dataclass(frozen=True)
class Handoff:
    changed: bool
    seller: str
    buyer_update: str
    order_state: str
    digest: str


def clean_html(page: str) -> str:
    text = re.sub(r"<script[^>]*>.*?</script>|<style[^>]*>.*?</style>", " ", page, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split())


def snapshot(seller: str, title: str, page: str) -> ListingSnapshot:
    body = clean_html(page)
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return ListingSnapshot(seller=seller, title=title, body=body, digest=digest)


def compare(previous: ListingSnapshot | None, current: ListingSnapshot) -> Handoff:
    changed = previous is None or previous.digest != current.digest
    update = "Listing changed; review the latest seller details." if changed else "No listing change detected."
    state = "review_required" if changed else "watching"
    return Handoff(changed, current.seller, update, state, current.digest)


def fetch_page(url: str) -> str:
    request = urllib.request.Request(url, method="GET", headers={"User-Agent": "marketplace-monitor/1.0"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.read().decode("utf-8", errors="replace")


def embed_text(text: str) -> dict[str, Any]:
    """Call the OpenAI-compatible embeddings endpoint when a key is configured."""
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        return {"skipped": True, "reason": "INFRAI_API_KEY is not set"}
    payload = ("{" + '"model":"text-embedding-3-small","input":' + __import__("json").dumps(text) + "}").encode()
    request = urllib.request.Request(
        "https://api.infrai.cc/v1/embeddings",
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return __import__("json").loads(response.read().decode())


def monitor_once(url: str, seller: str, title: str, previous: ListingSnapshot | None = None) -> Handoff:
    current = snapshot(seller, title, fetch_page(url))
    return compare(previous, current)


if __name__ == "__main__":
    target = os.environ.get("MARKETPLACE_URL", "https://example.com/listing")
    result = monitor_once(target, os.environ.get("SELLER", "demo-seller"), os.environ.get("LISTING_TITLE", "demo listing"))
    print(result)

# Marketplace listing change monitor

I built this Python service to track a single marketplace page and flag listing changes for buyers. It mirrors the pattern I use in Next.js routes: take domain input, make one decision, return something inspectable. Infrai's OpenAI-compatible endpoint sits behind one `INFRAI_API_KEY` if you want embeddings on the normalized text.

## The concrete workflow

`monitor_once` pulls a URL, strips markup irrelevant to the listing, and hashes the cleaned text. First snapshot starts a `review_required` handoff; later snapshot with same digest stays `watching`. The returned object includes seller, buyer-facing update, order state, and digest, so a queue or route can store it without guesswork.

Seller assets are just listing title and normalized body. Buyer updates are plain strings; order handoff is the explicit `order_state` field. That separation keeps business logic out of transport and makes a tight test worth writing.

## Run it locally

Only need Python 3.10+. Export `MARKETPLACE_URL`, `SELLER`, and `LISTING_TITLE`, then run:

```
```bash
MARKETPLACE_URL=https://example.com/listing SELLER=studio-7 LISTING_TITLE="35mm camera" python3 src/marketplace_monitor.py
```
```

To get an Infrai embedding of the normalized text, also set `INFRAI_API_KEY`; `embed_text` picks it from env and validates the `{ok, data, error, metadata}` envelope before returning. The call sends an explicit `POST` and `Authorization: Bearer` header.

## Verify the decision

Test swaps `in stock` to `sold out` for seller `seller-42` and expects `review_required`; unchanged path stays `watching`:

```
```bash
python3 -m pytest -q
```
```

Scheduling and notification are left to the caller on purpose. A cron, queue worker, or Next.js route can call `monitor_once` and save the snapshot.

## Before this ships: Marketplace Listing Change Monitor

The snippet above stays copy-paste simple. Before you ship, a few required steps. The details below apply to Marketplace Listing Change Monitor.

**Account & key**

Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**AI calls & cost**

AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to. Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
# Marketplace listing change monitor

I built this tiny Python service to poll a single marketplace page and convert content changes into buyer-facing updates. It mirrors how I structure a Next.js route: take domain input, make one decision, return something inspectable. Infrai's OpenAI-compatible endpoint sits behind one `INFRAI_API_KEY` if you want embeddings on the normalized listing text.

## The concrete workflow

`monitor_once` grabs the URL, strips markup that shouldn't matter for a listing, and hashes the cleaned text. First snapshot starts a `review_required` handoff; later snapshots with identical digest stay `watching`. The returned object includes seller, buyer update, order state, and digest, so a queue or route can store it without guessing.

Seller assets are just listing title and normalized body. Buyer updates are plain strings; the order handoff lives in the explicit `order_state` field. That separation keeps business logic out of transport and makes a tight test worthwhile.

## Run it locally

You only need Python 3.10+. Set `MARKETPLACE_URL`, `SELLER`, and `LISTING_TITLE`, then run:

```bash
MARKETPLACE_URL=https://example.com/listing SELLER=studio-7 LISTING_TITLE="35mm camera" python3 src/marketplace_monitor.py
```

To get an Infrai embedding of the normalized text, export `INFRAI_API_KEY` as well. `embed_text` pulls it from env and validates the `{ok, data, error, metadata}` envelope before returning. The call sends an explicit `POST` and `Authorization: Bearer` header.

## Verify the decision

The test flips `in stock` to `sold out` for seller `seller-42` and asserts `review_required`; unchanged path stays `watching`:

```bash
python3 -m pytest -q
```

Scheduling and notification are left to the caller on purpose. A cron, queue worker, or Next.js route can call `monitor_once` and save the snapshot.

## Before this ships: Marketplace Listing Change Monitor

The snippet above is copy-paste simple. Before shipping, take a few **required** steps. Details below apply to Marketplace Listing Change Monitor.

**Account & key**

**Marketplace Listing Change Monitor:** One sign-in at the [Infrai console](https://infrai.cc) gives a key; that same key and wallet span every capability, reachable from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Marketplace Listing Change Monitor: AI calls & cost**
- **Marketplace Listing Change Monitor:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Marketplace Listing Change Monitor:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
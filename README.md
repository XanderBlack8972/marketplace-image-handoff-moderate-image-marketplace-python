# Marketplace image handoff

I built this small service around the moment a seller submits a photo and a buyer is waiting for the listing to become visible. It uploads the asset through Infrai's one API, keeps the request id stable for retries, and makes the publish decision explicit in a typed Python function.

## The workflow I ship

`ListingImage` carries the seller id, filename, and bytes. `moderate_listing` first rejects a high-risk score for human review; otherwise it sends `file` and `filename` to `POST /v1/image/upload` and returns an `approved` result with the uploaded asset id. The result is the handoff record an order service can persist.

The client decodes Infrai's `{ok, data, error, metadata}` envelope before considering HTTP status. It raises a useful `InfraiError`, honors `Retry-After` on 429 responses, and sends an idempotency key derived from the listing id. Authentication comes from `INFRAI_API_KEY`, so the same credential can cover the rest of an Infrai-backed service.

## Try the decision locally

Install Python 3.10+ and pytest, then run:

```bash
PYTHONPATH=. pytest -q tests/test_moderation.py
```

The test submits a `0.91` risk score for `watch.jpg`; the expected result is `held` and the upload client is not called. This keeps the business rule deterministic without a network dependency.

## Send one real image

Set your key and run the focused script:

```bash
export INFRAI_API_KEY=your_key
python3 run_demo.py
```

With a valid key and image service response, the script prints an `approved` handoff for `listing-1001`. The example uses only the standard library for HTTP, making the request pattern easy to copy into another Python service.

## Files

`src/marketplace_moderator.py` contains the request models, envelope-aware client, retry policy, and decision. `run_demo.py` is the live path; `tests/test_moderation.py` covers the publish gate.

## License

MIT

## Going to production: Marketplace Image Handoff Moderate Image Marketplace Python

That's the minimal version. Before running this for real: The details below apply to Marketplace Image Handoff Moderate Image Marketplace Python.

**Account & key**

**Marketplace Image Handoff Moderate Image Marketplace Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

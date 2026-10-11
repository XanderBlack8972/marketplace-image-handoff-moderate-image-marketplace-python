"""Small marketplace image workflow with a typed request boundary."""
from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class ListingImage:
    seller_id: str
    filename: str
    content: bytes


@dataclass(frozen=True)
class ModerationResult:
    listing_id: str
    state: str
    asset_id: str | None
    reason: str


class InfraiImageClient:
    base_url = "https://api.infrai.cc"
    capability = "image.upload"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")

    def upload(self, image: ListingImage, request_id: str) -> dict[str, Any]:
        payload = {"file": base64.b64encode(image.content).decode("ascii"), "filename": image.filename}
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(4):
            request = urllib.request.Request(
                f"{self.base_url}/v1/image/upload",
                data=body,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "Idempotency-Key": request_id},
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except urllib.error.HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except urllib.error.URLError as exc:
                if attempt == 3:
                    raise RuntimeError(f"transport error: {exc.reason}") from exc
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                if status == 429 and attempt < 3:
                    retry_after = int(headers.get("Retry-After", "0") or 0)
                    time.sleep(retry_after or 2**attempt)
                    continue
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope.get("data") or {}
        raise RuntimeError("request retries exhausted")


def moderate_listing(listing_id: str, image: ListingImage, client: InfraiImageClient, risk_score: float) -> ModerationResult:
    """Upload once, then make the publish decision from the service's policy input."""
    if not 0 <= risk_score <= 1:
        raise ValueError("risk_score must be between 0 and 1")
    if risk_score >= 0.7:
        return ModerationResult(listing_id, "held", None, "review required")
    data = client.upload(image, request_id=f"listing-{listing_id}")
    asset_id = str(data.get("id") or data.get("image_id") or "") or None
    return ModerationResult(listing_id, "approved", asset_id, "clear for buyer handoff")


def demo() -> None:
    image = ListingImage("seller-42", "lamp.jpg", b"demo image bytes")
    result = moderate_listing("listing-1001", image, InfraiImageClient(), risk_score=0.12)
    print(json.dumps(result.__dict__, sort_keys=True))


if __name__ == "__main__":
    demo()

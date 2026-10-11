from src.marketplace_moderator import ListingImage, moderate_listing


class StubClient:
    def __init__(self):
        self.calls = []

    def upload(self, image, request_id):
        self.calls.append((image.filename, request_id))
        return {"id": "asset-7"}


def test_high_risk_listing_is_held_before_upload():
    client = StubClient()
    image = ListingImage("seller-1", "watch.jpg", b"bytes")
    result = moderate_listing("listing-9", image, client, risk_score=0.91)
    assert result.state == "held"
    assert result.reason == "review required"
    assert client.calls == []

import os
import struct
import zlib

from src.marketplace_moderator import ListingImage, InfraiImageClient, moderate_listing


def sample_png():
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    header = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(b"\x00\xff\xd0\x80")) + chunk(b"IEND", b"")


if __name__ == "__main__":
    if not os.environ.get("INFRAI_API_KEY"):
        raise SystemExit("Set INFRAI_API_KEY before running the live demo")
    image = ListingImage("seller-42", "sample.png", sample_png())
    print(moderate_listing("listing-1001", image, InfraiImageClient(), 0.12))

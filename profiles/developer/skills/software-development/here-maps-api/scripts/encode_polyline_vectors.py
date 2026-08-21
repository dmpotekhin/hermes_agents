#!/usr/bin/env python3
"""Mint polyline test-vector constants (flexible + Google) from coordinates.

Independent encoders written from the format specs — use them to produce
constants for decoder tests, or to cross-check a decoder round-trip.

Usage:
    python3 encode_polyline_vectors.py
Prints both encodings for a sample route and self-verifies nothing (decoders
live in the consumer project). Coordinates are (lat, lon) tuples as input.
"""
from __future__ import annotations

FLEX_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
GOOGLE_ALPHABET = "".join(chr(c) for c in range(63, 127))  # ord(char) - 63


def _enc_u(value: int, alphabet: str) -> str:
    out = []
    while value >= 0x20:
        out.append(alphabet[0x20 | (value & 0x1F)])
        value >>= 5
    out.append(alphabet[value])
    return "".join(out)


def _enc_signed(value: int, alphabet: str) -> str:
    n = value << 1
    if n < 0:
        n = ~n
    return _enc_u(n, alphabet)


def encode_flexible(coords: list[tuple[float, float]], precision: int = 5) -> str:
    """(lat, lon) pairs -> HERE flexible polyline (2D, no third dim)."""
    factor = 10**precision
    parts = [_enc_u(1, FLEX_ALPHABET), _enc_u(precision, FLEX_ALPHABET)]
    prev_lat = prev_lng = 0
    for lat, lng in coords:
        lat_i, lng_i = round(lat * factor), round(lng * factor)
        parts.append(_enc_signed(lat_i - prev_lat, FLEX_ALPHABET))
        parts.append(_enc_signed(lng_i - prev_lng, FLEX_ALPHABET))
        prev_lat, prev_lng = lat_i, lng_i
    return "".join(parts)


def encode_google(coords: list[tuple[float, float]], precision: int = 5) -> str:
    """(lat, lon) pairs -> Google polyline (OSRM geometry), no header."""
    factor = 10**precision
    parts = []
    prev_lat = prev_lng = 0
    for lat, lng in coords:
        lat_i, lng_i = round(lat * factor), round(lng * factor)
        parts.append(_enc_signed(lat_i - prev_lat, GOOGLE_ALPHABET))
        parts.append(_enc_signed(lng_i - prev_lng, GOOGLE_ALPHABET))
        prev_lat, prev_lng = lat_i, lng_i
    return "".join(parts)


if __name__ == "__main__":
    # sample: Moscow -> near-Moscow (matches the verified HERE test vector shape)
    sample = [(52.50259, 13.38933), (52.50339, 13.39098), (52.50419, 13.39080)]
    print("flexible:", encode_flexible(sample))
    print("google:  ", encode_google(sample))

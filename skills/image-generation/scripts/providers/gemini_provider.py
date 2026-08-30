"""Gemini image models, through the Interactions API.

Gemini takes an aspect ratio and a size class rather than an explicit pixel
size, so a WxH request is mapped to the closest supported ratio.
"""
from __future__ import annotations

import base64
from math import gcd
from pathlib import Path

from .base import Provider, ProviderError, Request, Result, post_json, register, require_key

INTERACTIONS_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
RATIOS = ("1:1", "16:9", "3:2", "9:16", "4:3", "3:4", "4:5", "5:4", "21:9", "2:3")
SIZES = ("512px", "1K", "2K", "4K")


class GeminiProvider:
    name = "gemini"
    default_model = "gemini-3-pro-image"
    key_env = "GEMINI_API_KEY"

    def run(self, request: Request) -> Result:
        key = require_key(self.key_env)
        model = request.model or self.default_model
        inputs: list[dict] = [{"type": "text", "text": request.prompt}]
        for path in request.references:
            if not path.is_file():
                raise ProviderError(f"reference image not found: {path}")
            inputs.append(
                {
                    "type": "image",
                    "mime_type": _mime(path),
                    "data": base64.b64encode(path.read_bytes()).decode("ascii"),
                }
            )
        payload = post_json(
            INTERACTIONS_URL,
            {
                "model": model,
                "input": inputs,
                "response_format": {
                    "type": "image",
                    "mime_type": f"image/{'jpeg' if request.output_format == 'jpeg' else 'png'}",
                    "aspect_ratio": aspect_ratio(request.size),
                    "image_size": request.extra.get("image_size", "1K"),
                },
            },
            {"x-goog-api-key": key},
        )
        return Result(images=_extract(payload), usage=payload.get("usage") or {})


def aspect_ratio(size: str) -> str:
    if ":" in size:
        return size if size in RATIOS else "1:1"
    if "x" not in size:
        return "1:1"
    width, height = (int(part) for part in size.lower().split("x", 1))
    divisor = gcd(width, height)
    candidate = f"{width // divisor}:{height // divisor}"
    return candidate if candidate in RATIOS else "1:1"


def _mime(path: Path) -> str:
    return "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"


def _extract(payload: dict) -> tuple[bytes, ...]:
    direct = (payload.get("output_image") or {}).get("data")
    if direct:
        return (base64.b64decode(direct),)
    images: list[bytes] = []
    for step in payload.get("steps") or []:
        for item in step.get("output") or []:
            data = item.get("data") if item.get("type") == "image" else None
            if data:
                images.append(base64.b64decode(data))
    if not images:
        raise ProviderError(f"no image in Gemini response: {str(payload)[:400]}")
    return tuple(images)


register("gemini", GeminiProvider)

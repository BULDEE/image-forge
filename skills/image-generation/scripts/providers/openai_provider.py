"""OpenAI GPT Image, through the images endpoints.

Two paths: generations when no reference is given, edits when one or more
reference images are passed. References are the reliable way to hold a style
across a series; repeating a style paragraph in prose drifts after a few
renders.
"""
from __future__ import annotations

import base64
import mimetypes
import uuid
from pathlib import Path

from .base import Provider, ProviderError, Request, Result, post_json, post_raw, register, require_key

GENERATIONS_URL = "https://api.openai.com/v1/images/generations"
EDITS_URL = "https://api.openai.com/v1/images/edits"


class OpenAIProvider:
    name = "openai"
    default_model = "gpt-image-2"
    key_env = "OPENAI_API_KEY"

    def run(self, request: Request) -> Result:
        key = require_key(self.key_env)
        model = request.model or self.default_model
        headers = {"Authorization": f"Bearer {key}"}
        if request.references:
            payload = self._edit(request, model, headers)
        else:
            payload = post_json(
                GENERATIONS_URL,
                {
                    "model": model,
                    "prompt": request.prompt,
                    "size": request.size,
                    "quality": request.quality,
                    "background": request.background,
                    "output_format": request.output_format,
                    "n": request.count,
                },
                headers,
            )
        return _to_result(payload)

    def _edit(self, request: Request, model: str, headers: dict) -> dict:
        missing = [str(p) for p in request.references if not p.is_file()]
        if missing:
            raise ProviderError(f"reference image not found: {', '.join(missing)}")
        boundary = uuid.uuid4().hex
        fields = {
            "model": model,
            "prompt": request.prompt,
            "size": request.size,
            "quality": request.quality,
            "n": str(request.count),
        }
        mask = request.extra.get("mask")
        body = bytearray()
        for name, value in fields.items():
            body += f"--{boundary}\r\n".encode()
            body += f'Content-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
        for path in request.references:
            body += _file_part(boundary, "image[]", path)
        if mask:
            body += _file_part(boundary, "mask", Path(mask))
        body += f"--{boundary}--\r\n".encode()
        return post_raw(
            EDITS_URL,
            bytes(body),
            {**headers, "Content-Type": f"multipart/form-data; boundary={boundary}"},
        )


def _file_part(boundary: str, field: str, path: Path) -> bytes:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    head = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{field}"; filename="{path.name}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode()
    return head + path.read_bytes() + b"\r\n"


def _to_result(payload: dict) -> Result:
    items = payload.get("data") or []
    if not items:
        raise ProviderError(f"no image in response: {str(payload)[:400]}")
    images = []
    for item in items:
        encoded = item.get("b64_json")
        if not encoded:
            raise ProviderError("response carried no b64_json payload")
        images.append(base64.b64decode(encoded))
    return Result(
        images=tuple(images),
        usage=payload.get("usage") or {},
        revised_prompt=(items[0].get("revised_prompt") if items else None),
    )


register("openai", OpenAIProvider)

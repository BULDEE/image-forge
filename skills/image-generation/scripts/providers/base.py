"""Provider contract shared by every image backend.

A provider turns a Request into raw image bytes. It never writes files, never
prints, and never reads a credential from anywhere but the environment, so a
secret manager wrapper stays the only path to a key.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Protocol

TIMEOUT_SECONDS = 300


class ProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class Request:
    prompt: str
    model: str | None = None
    size: str = "1024x1024"
    quality: str = "high"
    background: str = "opaque"
    output_format: str = "png"
    count: int = 1
    references: tuple[Path, ...] = ()
    extra: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Result:
    images: tuple[bytes, ...]
    usage: dict = field(default_factory=dict)
    revised_prompt: str | None = None


class Provider(Protocol):
    name: str
    default_model: str
    key_env: str

    def run(self, request: Request) -> Result: ...


_REGISTRY: dict[str, Callable[[], Provider]] = {}


def register(name: str, factory: Callable[[], Provider]) -> None:
    _REGISTRY[name] = factory


def available() -> tuple[str, ...]:
    return tuple(sorted(_REGISTRY))


def get(name: str) -> Provider:
    if name not in _REGISTRY:
        raise ProviderError(f"unknown provider '{name}'; available: {', '.join(available())}")
    return _REGISTRY[name]()


def require_key(env_name: str) -> str:
    key = os.environ.get(env_name, "").strip()
    if not key:
        raise ProviderError(
            f"{env_name} is not set. Run the command through the secret manager wrapper "
            f"so the value never reaches the shell history."
        )
    return key


def post_json(url: str, payload: dict, headers: dict) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    return _send(request)


def post_raw(url: str, body: bytes, headers: dict) -> dict:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    return _send(request)


def _send(request: urllib.request.Request) -> dict:
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")[:800]
        raise ProviderError(f"HTTP {error.code} from {request.full_url}: {detail}") from error
    except urllib.error.URLError as error:
        raise ProviderError(f"network failure calling {request.full_url}: {error.reason}") from error

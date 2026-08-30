#!/usr/bin/env python3
"""Image Forge: render, inspect and review images from the terminal.

Credentials are read from the environment only, so the process is meant to be
launched through a secret manager wrapper. Every render writes a sidecar JSON
next to the image holding the exact prompt and parameters, because an image
whose prompt was lost cannot be iterated on, only replaced.
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pngtools  # noqa: E402
from providers import ProviderError, Request, available, get  # noqa: E402


def render(args: argparse.Namespace) -> int:
    prompt = _read_prompt(args)
    out = Path(args.out).expanduser()
    request = Request(
        prompt=prompt,
        model=args.model,
        size=args.size,
        quality=args.quality,
        background=args.background,
        output_format=args.format,
        count=args.n,
        references=tuple(Path(p).expanduser() for p in args.ref),
        extra={"mask": args.mask, "image_size": args.image_size},
    )
    provider = get(args.provider)
    result = provider.run(request)
    written = _write_images(result.images, out)
    for path in written:
        if args.hard_alpha is not None:
            snapped = pngtools.harden_alpha(path, args.hard_alpha)
            print(f"hard alpha: {snapped} feathered pixels snapped at threshold {args.hard_alpha}")
        print(f"{path}  {path.stat().st_size} bytes")
        if args.preview:
            preview = path.with_name(f"{path.stem}-{args.preview}px{path.suffix}")
            pngtools.downscale(path, args.preview, preview)
            print(f"{preview}  preview {args.preview}px")
    sidecar = written[0].with_suffix(".json")
    sidecar.write_text(
        json.dumps(
            {
                "provider": args.provider,
                "model": args.model or provider.default_model,
                "prompt": prompt,
                "size": args.size,
                "quality": args.quality,
                "background": args.background,
                "references": [str(p) for p in request.references],
                "revised_prompt": result.revised_prompt,
                "usage": result.usage,
                "files": [str(p) for p in written],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"{sidecar}  prompt and parameters")
    if result.revised_prompt:
        print(f"revised prompt: {result.revised_prompt}")
    if result.usage:
        print(f"usage: {json.dumps(result.usage, sort_keys=True)}")
    return 0


def inspect(args: argparse.Namespace) -> int:
    for name in args.images:
        path = Path(name).expanduser()
        width, height, _ = pngtools.read_rgba(path)
        report = pngtools.alpha_report(path)
        total = width * height
        share = 100 * report["feathered"] / total if total else 0
        print(
            f"{path}  {width}x{height}  opaque={report['opaque']} "
            f"transparent={report['transparent']} feathered={report['feathered']} ({share:.1f}%)"
        )
    return 0


def sheet(args: argparse.Namespace) -> int:
    cards = []
    for name in args.images:
        path = Path(name).expanduser()
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        cards.append(
            f'<figure><img src="data:image/png;base64,{encoded}" alt="{path.stem}">'
            f'<img class="small" src="data:image/png;base64,{encoded}" alt="{path.stem} small">'
            f"<figcaption>{path.stem}</figcaption></figure>"
        )
    out = Path(args.out).expanduser()
    out.write_text(_SHEET_TEMPLATE.replace("<!--CARDS-->", "\n".join(cards)), encoding="utf-8")
    print(f"{out}  contact sheet with {len(cards)} image(s)")
    return 0


_SHEET_TEMPLATE = """<title>Contact sheet</title>
<style>
:root { color-scheme: light dark; --ink:#111; --paper:#faf9f7; --line:#d8d5d0; }
@media (prefers-color-scheme: dark) { :root { --ink:#eee; --paper:#15161a; --line:#33353c; } }
body { margin:0; padding:32px; background:var(--paper); color:var(--ink);
       font:14px/1.5 system-ui, sans-serif; }
main { display:grid; gap:24px; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); }
figure { margin:0; border:1px solid var(--line); border-radius:12px; padding:12px;
         display:grid; gap:8px; justify-items:center; }
figure img { width:100%; height:auto; border-radius:8px; }
figure img.small { width:32px; height:32px; image-rendering:auto; }
figcaption { font-size:12px; opacity:.7; }
</style>
<h1>Contact sheet</h1>
<p>Each card shows the render and the same file at 32 pixels. Judge the small one.</p>
<main>
<!--CARDS-->
</main>
"""


def providers(_: argparse.Namespace) -> int:
    for name in available():
        print(name)
    return 0


def _read_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file:
        text = Path(args.prompt_file).expanduser().read_text(encoding="utf-8").strip()
    else:
        text = (args.prompt or "").strip()
    if not text:
        raise ProviderError("empty prompt: pass --prompt or --prompt-file")
    return text


def _write_images(images: tuple[bytes, ...], out: Path) -> list[Path]:
    out.parent.mkdir(parents=True, exist_ok=True)
    if len(images) == 1:
        out.write_bytes(images[0])
        return [out]
    written = []
    for index, blob in enumerate(images, start=1):
        target = out.with_name(f"{out.stem}-{index}{out.suffix}")
        target.write_bytes(blob)
        written.append(target)
    return written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="forge", description="Render and review generated images.")
    sub = parser.add_subparsers(dest="command", required=True)

    render_parser = sub.add_parser("render", help="generate or edit an image")
    render_parser.add_argument("--provider", default="openai", choices=list(available()))
    render_parser.add_argument("--prompt")
    render_parser.add_argument("--prompt-file")
    render_parser.add_argument("--out", required=True)
    render_parser.add_argument("--model")
    render_parser.add_argument("--size", default="1024x1024")
    render_parser.add_argument("--quality", default="high", choices=["low", "medium", "high", "auto"])
    render_parser.add_argument(
        "--background", default="opaque", choices=["opaque", "transparent", "auto"]
    )
    render_parser.add_argument("--format", default="png", choices=["png", "jpeg", "webp"])
    render_parser.add_argument("--image-size", default="1K", help="Gemini size class")
    render_parser.add_argument("--n", type=int, default=1)
    render_parser.add_argument("--ref", action="append", default=[], metavar="IMAGE")
    render_parser.add_argument("--mask", metavar="PNG")
    render_parser.add_argument(
        "--hard-alpha", nargs="?", type=int, const=128, metavar="THRESHOLD",
        help="snap feathered transparency to binary alpha",
    )
    render_parser.add_argument("--preview", type=int, metavar="PX")
    render_parser.set_defaults(handler=render)

    inspect_parser = sub.add_parser("inspect", help="report size and alpha composition")
    inspect_parser.add_argument("images", nargs="+")
    inspect_parser.set_defaults(handler=inspect)

    sheet_parser = sub.add_parser("sheet", help="build an HTML contact sheet for review")
    sheet_parser.add_argument("images", nargs="+")
    sheet_parser.add_argument("--out", required=True)
    sheet_parser.set_defaults(handler=sheet)

    list_parser = sub.add_parser("providers", help="list registered providers")
    list_parser.set_defaults(handler=providers)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.handler(args)
    except (ProviderError, pngtools.PngError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

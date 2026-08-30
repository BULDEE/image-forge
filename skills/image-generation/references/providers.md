# Providers

## OpenAI GPT Image

Endpoints: `/v1/images/generations`, and `/v1/images/edits` when `--ref` is
passed. Key: `OPENAI_API_KEY`. Images always come back base64, never as a URL.

| Parameter | Values |
|---|---|
| model | `gpt-image-2` (default), `gpt-image-1.5`, `gpt-image-1`, `gpt-image-1-mini` |
| size | `1024x1024`, `1536x1024`, `1024x1536`, `auto`, or any pair of multiples of 16 within 655360 to 8294400 pixels, max edge 3840, max ratio 3:1 |
| quality | `low`, `medium`, `high`, `auto` |
| background | `opaque`, `transparent`, `auto` |
| output_format | `png`, `jpeg`, `webp` |
| n | images per request |

`gpt-image-2` always processes reference images at high fidelity, so the older
`input_fidelity` parameter no longer applies to it.

Masks are guidance, not a stencil: the model uses the mask's shape as a hint and
may not follow it exactly. A mask must be a PNG with an alpha channel, the same
dimensions as the image it edits.

### Transparency is preview quality

`--background transparent` returns a real RGBA file with fully transparent
corners, but the edges of flat shapes come back feathered. Measured on a flat
two-colour icon: **14.2 percent of pixels carried a partial alpha**, which reads
as a halo on a light surface.

Use `--hard-alpha` to snap alpha to binary, and `inspect` to confirm:

```bash
forge.py render ... --background transparent --hard-alpha
forge.py inspect out.png    # feathered must be 0
```

Do not use `--hard-alpha` on photographic or soft-edged art: there the
feathering is the anti-aliasing, and snapping it produces jagged edges.

### Cost

Billed per image plus output tokens. A 1024x1024 render costs about 7000 output
image tokens regardless of prompt length, so prompt iteration is nearly free and
re-rolls are not. Iterate composition at `--quality medium`, confirm at `high`.

## Gemini

Endpoint: `/v1beta/interactions`. Key: `GEMINI_API_KEY`. Models:
`gemini-3-pro-image` (default here), `gemini-3.1-flash-image`,
`gemini-3.1-flash-lite-image`, `gemini-2.5-flash-image`.

Gemini takes an **aspect ratio** and a **size class**, not pixels. `--size` is
converted to the nearest supported ratio; pass `--image-size` for the class
(`512px` on flash-lite only, `1K`, `2K`, `4K`). Supported ratios: 1:1, 16:9,
3:2, 9:16, 4:3, 3:4, 4:5, 5:4, 21:9, 2:3.

Reference images are sent inline as base64 in the same `input` array as the
text, which makes multi-reference conditioning natural here.

## MCP-backed generators

A CLI process cannot call an MCP tool: the connection belongs to the agent
session. These providers are registered so the routing question has an answer,
and they fail immediately with the handoff instruction rather than pretending a
transport exists.

Chain them explicitly: call the MCP tool, save the output, then pass that file
back with `--ref` when another provider has to match its style.

## Adding a provider

1. Create `scripts/providers/<name>_provider.py`.
2. Implement `run(self, request: Request) -> Result` with `name`,
   `default_model` and `key_env` class attributes.
3. Read the key with `require_key`, post with `post_json` or `post_raw` so
   error handling and timeouts stay uniform.
4. Call `register("<name>", <Class>)` at module scope and import the module in
   `providers/__init__.py`.

The provider returns bytes. It never writes files, never prints, and never
reads a credential from anywhere but the environment.

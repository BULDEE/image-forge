# Image Forge

A Claude Code plugin for producing images from the terminal: icons, avatars,
illustrations, mockups, social cards. It renders through OpenAI GPT Image,
Gemini, or an MCP-backed generator, writes every file next to the exact prompt
that produced it, and carries a review loop so a render is verified before a
whole set is generated.

## Why a plugin and not a chat window

A chat render cannot be re-run, diffed, versioned, or reviewed as a set. A file
can. Everything here follows from that: prompts live in files, renders carry a
sidecar JSON, and the contact sheet exists so a series is judged together
instead of one image at a time.

## Install

```bash
/plugin marketplace add BULDEE/image-forge
/plugin install image-forge
```

Or clone anywhere and point Claude Code at the directory.

## Configure

| Option | Purpose |
|---|---|
| `secret_command` | Command prefix that injects API keys, for example `doppler run --` |
| `default_provider` | `openai` or `gemini` |
| `output_dir` | Where renders land when no path is given |

Keys are read from the environment (`OPENAI_API_KEY`, `GEMINI_API_KEY`) and are
never printed by the tool.

## Use

```bash
forge.py render --prompt-file prompt.txt --out icon.png --preview 32
forge.py render --ref icon.png --prompt "Same style. The symbol is ..." --out icon-2.png
forge.py inspect icon.png
forge.py sheet out/*.png --out contact-sheet.html
forge.py providers
```

In a session, `/image <what you want>` runs the full loop: render, review,
iterate, report paths.

## What it knows that a bare API call does not

- **Transparency is preview quality.** `--background transparent` returns real
  alpha but feathers flat edges; measured at 14.2 percent partial-alpha pixels
  on a two-colour icon. `--hard-alpha` snaps it to binary, `inspect` proves it.
- **An icon is validated at the size it is displayed.** `--preview 32` writes
  the small file that decides.
- **Style holds through reference images, not through repeated prose.**
- **Anything described as faint becomes dominant**, and a plural plus "small"
  becomes mush. The prompting reference documents the failure modes with the
  fixes.

## Providers

| Provider | Transport | Key |
|---|---|---|
| `openai` | HTTPS, images endpoints | `OPENAI_API_KEY` |
| `gemini` | HTTPS, interactions endpoint | `GEMINI_API_KEY` |
| `higgsfield` | MCP tools, not this CLI | n/a |

Adding one is a single file implementing `run(request) -> Result`. See
`skills/image-generation/references/providers.md`.

## Requirements

Python 3.10 or later, standard library only. No image library needed: PNG
inspection, binary alpha and downscaling are implemented in `pngtools.py`.

## Licence

MIT.

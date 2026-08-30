---
name: image-generation
description: "Use whenever an image has to be produced or reworked: icons, avatars, logos, illustrations, mockups, social cards, thumbnails, textures, or a consistent set of any of those. Renders through OpenAI GPT Image, Gemini, or an MCP-backed generator, writes files to disk with their prompt, and runs a critique loop so the render is verified before a whole set is produced. Prefer this over asking the user to open a chat UI."
---

# Image generation

Render to a file, look at the file, decide, then produce the set. A chat UI
cannot be re-run, diffed, or versioned; a file next to its prompt can.

## Run

```bash
${CLAUDE_PLUGIN_ROOT}/skills/image-generation/scripts/forge.py render \
  --provider openai \
  --prompt-file /abs/path/prompt.txt \
  --out /abs/path/render.png \
  --preview 32
```

Subcommands: `render`, `inspect` (size and alpha composition), `sheet` (HTML
contact sheet for review), `providers` (list what is registered).

Every render writes `<out>.json` beside the image holding the exact prompt,
model and parameters. An image whose prompt was lost cannot be iterated on,
only replaced.

## Credentials

Keys are read from the environment and never printed. Launch through the
configured secret manager wrapper:

```bash
doppler run -- ${CLAUDE_PLUGIN_ROOT}/skills/image-generation/scripts/forge.py render ...
```

`OPENAI_API_KEY` for `openai`, `GEMINI_API_KEY` for `gemini`. If a key is
missing the command says which variable it wanted; do not work around it by
reading the secret into a shell variable.

A privacy guard may sit in front of the wrapper and refuse the command. It
matches text and does not parse shell, so three forms fail for reasons the
error message will not spell out:

- a redirection on the render (`... render > /tmp/forge.log`). The script
  already writes `<out>.json` beside the image; read that back instead.
- an explicit interpreter (`run -- python3 forge.py`). `forge.py` is
  executable; call it directly.
- a variable whose name reads as a secret (`$OPENAI_API_KEY` on the command
  line). Let the wrapper inject it; never name it yourself.

Chaining is fine: `&&`, a pipe, a heredoc written on an earlier line and a
backslash continuation all pass. The prompt file is the exception worth
knowing: write it in its own command when its text quotes shell commands, then
render with `--prompt-file`.

## Choosing a provider

| Provider | Reach for it when | Notes |
|---|---|---|
| `openai` | flat vector work, icons, precise instruction following, transparency | `gpt-image-2` default; `--background transparent` is preview-quality, see below |
| `gemini` | photographic scenes, wide aspect ratios, 4K output | size given as an aspect ratio plus a size class, not pixels |
| `higgsfield` | video and stylised motion work | reachable only through its MCP tools; the CLI fails with the handoff instruction |

An MCP-backed generator cannot be called from a CLI process: the connection
belongs to the agent session. Call its MCP tools directly, save the file, then
feed it back with `--ref` if it has to seed another provider.

## The loop that matters

1. **One render first.** Never generate a set from an unverified prompt.
2. **Read the file back** with the Read tool and judge it. The 1024px render is
   not the deliverable; the size it will be displayed at is. Use `--preview 32`
   for icons and look at the small file.
3. **Name the defect, not the vibe.** "Off-centre by roughly 4 percent" and
   "the background grid outweighs the subject" are actionable; "make it nicer"
   is not.
4. **Fix the prompt, re-render, compare.** One change at a time, or you cannot
   tell which change worked.
5. **Only then produce the set**, passing the accepted render as `--ref` so the
   style holds.

Read `references/critique-loop.md` before judging a render, and
`references/prompt-engineering.md` before writing one.

## References

- `references/prompt-engineering.md`: how to write a prompt that survives
  downscaling, and the failure modes that recur.
- `references/providers.md`: parameter matrices, transparency behaviour, cost,
  and how to add a provider.
- `references/critique-loop.md`: the review rubric and the adversarial chain.
- `references/series.md`: producing a consistent set: references, seeds, and
  what actually drifts.

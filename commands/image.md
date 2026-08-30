---
description: Render an image, review it, and iterate before producing a set.
---

Produce the image the user asked for, using the `image-generation` skill.

Follow its loop without shortcuts:

1. Write the prompt to a file next to where the image will land.
2. Render one image with `forge.py render`, adding `--preview 32` when the
   target is an icon or an avatar.
3. Read the rendered file back and judge it against the rubric in
   `references/critique-loop.md`. Name the dominant defect explicitly.
4. Fix one thing, re-render, compare. Stop when the rubric passes or when two
   re-rolls fail the same way, which means the prompt is at fault.
5. Report the absolute path of every file written, so the user can open it.

Never generate a set from an unverified prompt.

$ARGUMENTS

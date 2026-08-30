# Prompt engineering for images

An image prompt is a specification, not a wish. The model fills every gap you
leave, and it fills them with decoration.

## Structure

Write in this order. Each part answers a question the model would otherwise
answer on its own.

1. **Medium and treatment**: "a flat vector app icon", "a photograph shot on
   85mm", "a technical isometric diagram". This is the single highest-leverage
   token group.
2. **Ground**: "on a full-bleed deep charcoal background", "on a fully
   transparent background, no background shape of any kind".
3. **Composition**: centred, symmetrical, margins, what occupies what share of
   the frame. Give proportions as percentages; the model honours them roughly
   and ignores them entirely if unstated.
4. **Subject, described as geometry**: shapes, counts, relations.
5. **Palette**: exact hex values, and how many colours are allowed.
6. **Constraints**: stroke weight, shape budget, the size it must survive.
7. **Exclusions**: the short list of things that keep creeping in.

## The rules that are not obvious

**Anything you call faint, subtle, or background becomes dominant.** There is no
reliable way to ask for a discreet element. If it should be quiet, remove it
from the prompt entirely, or accept it as a co-star.

**Plurals plus "small" produce mush.** "a constellation of nodes", "a ring of
small drums" render as texture that dissolves on downscale. Name an exact
count: "exactly three connected dots", "one large drum".

**Naming an entity imports its iconography.** "Kitsune, a Japanese fox spirit"
pulls in fur, torii gates and painterly detail. "a geometric fox mask with
three tails" does not. Describe the form; keep the name in the filename.

**Beyond four distinct shapes an icon stops surviving downscaling.** State the
budget in the prompt: "four shapes maximum".

**Negations work, but only for things the model was about to do.** A list of
twenty exclusions wastes tokens and dilutes the positive description. Keep the
exclusion list to the failures you actually observed.

**Text rendering is still unreliable.** Precise typography and exact placement
remain weak in every current model. If the image must carry text, compose the
text yourself over a rendered background rather than asking for it.

**Over-correction is the second failure.** Strip too much and a distinctive
symbol becomes a generic pictogram. The fix for a busy icon is a shape budget
and a hierarchy, not the removal of everything that made it recognisable.

## Composition control

Symmetry, centring and equal margins are requested, not guaranteed. Current
models drift a few percent off-centre even when told to be symmetrical. Treat
that as a crop-time correction, not a prompt problem; re-rolling for centring
burns tokens and usually returns a different drift.

## Style consistency

A style paragraph repeated in prose drifts after a few renders. A reference
image does not. Produce one accepted render, then pass it with `--ref` for
every sibling. See `series.md`.

## Reproducibility

The renderer writes a sidecar JSON with the exact prompt and parameters. Keep
prompts in files under version control, one file per image, named after the
output. When a render is wrong, you want to diff the prompt that produced it,
not reconstruct it from memory.

Some APIs return a `revised_prompt`: the model's rewritten version of your text.
When present it is printed and stored in the sidecar. If it differs sharply from
what you wrote, that difference explains the render.

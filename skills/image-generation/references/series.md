# Producing a consistent set

Sets fail on drift: image seven no longer looks like image one. Three things
control it, in decreasing order of effectiveness.

## 1. A locked reference image

Produce one image, accept it, freeze it as the style reference, and pass it to
every sibling:

```bash
forge.py render --ref reference/style-reference.png \
  --prompt "Same treatment, same palette weight, same stroke width and shape budget as the reference. The symbol is <geometry>." \
  --out out/second.png
```

The reference carries stroke weight, colour temperature and margin far more
reliably than any sentence.

## 2. A literal style block

When references are unavailable, repeat the style paragraph **verbatim**
between renders. Rewording it, even improving it, is what causes drift. Keep
that block in one file and concatenate it with the per-image subject block.

## 3. One subject sentence per image

Vary only the subject. If two images differ in composition rules, palette count
or stroke weight, they will not read as a set no matter how good each one is.

## Review the set, not the images

Build a contact sheet and judge them together:

```bash
forge.py sheet out/*.png --out out/contact-sheet.html
```

Each card shows the render and the same file at 32 pixels. A set is coherent
when the small versions look like siblings, which is a stricter test than the
large ones passing individually.

## What to freeze in writing

Alongside the reference image, keep a plain note recording the palette hexes,
the shape budget, the background treatment and the accepted margins. The next
person to extend the set six months later has the reference file but not the
reasoning.

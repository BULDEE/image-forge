# Critique loop

The agent can see the image it just produced. Use that: read the file back and
judge it against a rubric before spending anything on a set.

## Rubric

Score each, and name the failing one explicitly.

1. **Legibility at target size.** For an icon, look at the `--preview 32` file,
   not the full render. If the symbol dissolves, nothing else matters.
2. **Shape budget.** Count the distinct shapes. More than four in an icon is a
   downscaling failure waiting to happen.
3. **Hierarchy.** Does the intended subject dominate, or has a background
   element taken over?
4. **Specificity.** Does it read as the thing asked for, or as a generic
   pictogram that could stand for anything? Over-correction lands here.
5. **Composition.** Centring, margins, symmetry where symmetry was asked for.
6. **Palette discipline.** Count the colours actually used against the number
   allowed.
7. **Edges.** For transparent output, run `inspect`: feathered pixels above a
   percent or so mean a halo on light surfaces.

## One change at a time

When two things are wrong, fix the one that dominates, re-render, and look
again. Changing composition and palette in the same iteration makes the next
render uninterpretable: you cannot tell which edit helped.

## Adversarial chain

For work that has to hold up, split generation from judgement:

- **Generator** renders with provider A.
- **Critic** is a separate pass that only names defects against the rubric,
  with no authority to praise. A second provider, a subagent, or the same
  session in a distinct step all work; what matters is that the critique step
  is not allowed to produce the image it is judging.
- **Referee** decides whether to re-render, adjust the prompt, or accept.

Chain across providers when their strengths differ: a photographic base from
one, a flat overlay from another, an animated variant from an MCP-backed
generator, each step feeding the next as a reference file.

## Stop conditions

Stop when the rubric passes, or when two consecutive re-rolls fail the same way
without the prompt changing. The second case means the prompt is the problem,
not the sampling; rewriting it beats another roll.

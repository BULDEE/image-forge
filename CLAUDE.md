# Contributing to image-forge

Rules an agent or a human must follow when changing this repository. They are
not style preferences: a change that breaks one of them is rejected, however
well it works.

## Language

Everything written into the repository is in **English**: code, comments,
documentation, commit messages, issue and pull request text. No exception.

Never use an em-dash (U+2014) anywhere. Use a colon, a full stop, a comma,
parentheses, or restructure the sentence.

## Python

- Standard library only. This tool has to run inside a container with no
  package installation step, so a new third-party import is a design change,
  not a detail.
- `from __future__ import annotations` at the top of every module.
- Type hints on every function signature.
- No bare `except`. Catch the specific exception, and re-raise with context
  using `raise ... from error`.
- No explanatory comment that restates the code. A comment earns its place only
  by recording a decision, a measurement, or a trap that the code cannot show.
- Functions stay small and single-purpose. A helper prefixed with `_` is
  private to its module.
- Maximum three positional parameters. Beyond that, pass an object.

## Layering

- `providers/` never writes files, never prints, and never reads a credential
  from anywhere but the environment.
- `pngtools.py` knows nothing about providers or the network.
- `forge.py` is the only module allowed to touch the filesystem for output and
  to print to stdout.

A change that makes a provider write a file, or `pngtools` call an API, is a
layering violation.

## Secrets

API keys are read from environment variables only. Never write a key to disk,
never print one, never accept one as a command-line argument, and never include
one in an error message. Error text that echoes a request URL must not carry a
credential in that URL: pass keys in headers.

## Tests

- A behavioural change comes with a test. A test asserts behaviour, not
  implementation.
- One concept per test, arranged as arrange, act, assert.
- Tests use the standard library `unittest` and run with
  `python3 -m unittest discover -s tests`.
- A test that has never been seen to fail proves nothing: when fixing a bug,
  write the failing test first and watch it fail.

## Verification before claiming completion

Never report a change as done on the strength of the code reading correctly.
Run it. For this repository that means, at minimum, `python3 -m unittest
discover -s tests` and, for anything touching a provider or the CLI surface,
`forge.py --help` plus the affected subcommand on a real file.

## Commits

- Conventional Commits: `type(scope): description`, in the imperative.
- One logical change per commit.
- Never add a `Co-Authored-By` trailer, and never mention an AI tool, an agent,
  or a model anywhere in the commit message, the branch name, or the pull
  request body.

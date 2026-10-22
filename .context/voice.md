# Voice

The project dials for `.claude/rules/prose-core.md`. That rule is the baseline. This file tightens it
for WhoIsOnFirst and names the exemptions.

## Audience and register

- The UI and SMS text are for on-call staff. They read it on a phone, often in a hurry.
- The code, comments and `.context/` are for the maintainer.
- The register is plain and operational. State what happened or what to do. No exclamation marks.

## Comments and docstrings

- Use Google-style docstrings (`Args:`, `Returns:`, `Raises:`) only on public service methods and API
  route functions.
- A repository method or other trivial method gets a docstring of one line, with no `Args:` or `Returns:`
  block.
- Write a comment only for a constraint the code cannot show. The comment budget is about one comment
  line for every five code lines.

## README

- Keep the README short: what the app does, how to run it, where the docs are.
- Write it for a new maintainer. Do not add marketing language.

## UI copy

- A success message names the result in two to four words: "Shift added.", "Template saved."
- An error message starts with "Could not" and the action, then gives the server detail or the next
  step: "Could not load schedules. Reload the page."
- A confirm dialog names the action and its effect. Add "You cannot undo this." when that is true.
- Do not put emoji or warning glyphs in alert, confirm or toast text. Use the Tabler icon classes
  (`ti ti-check`, `ti ti-alert-circle`) for visual status.

## SMS text

- One statement per message: who is on call, from when, until when.
- No emoji and no exclamation marks.
- Every time states the time zone.

## Exemptions

- The Abbott and Costello easter egg on `login.html` quotes the routine. It keeps its punctuation and emoji.
- The dashboard placeholder "What's on second?" is the app's name joke. Keep the question; end the
  answer with a full stop.
- Log lines quoted in `help.html` match the server logs word for word.
- Design tools that keep their own context file point at this file. They do not copy it.

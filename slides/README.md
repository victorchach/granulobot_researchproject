# Meeting slides

Slides for the regular meetings with the supervisor, written with
[Marp](https://marp.app/) (Markdown to PDF, PPTX or HTML). There is one deck
per theme:

| Deck | Theme |
| --- | --- |
| [`1-context.md`](1-context.md) | Granulobots, the assignment, goal, roadmap |
| [`2-model.md`](2-model.md) | how the simulator works, for a physicist: bodies, forces, contacts, time step, parameters and limits |
| [`3-architecture.md`](3-architecture.md) | code architecture, version by version, and the workflow |
| [`4-results.md`](4-results.md) | results, in the order of [`results/journal.md`](../results/journal.md) |

The decks tell a coherent story. A real evolution (a new architecture, a new
model) gets a new versioned slide after the old one, so the decks show how the
project evolved. A slide that turns out wrong or out of date is fixed in place.
The results deck follows our reasoning from one run to the next. Each slide
says in its footer when it was added, and when it was revised. The `slides` skill
(`.agents/skills/slides/SKILL.md`) holds the rules and the commands.

- `theme/granulobot.css`: the theme (white, the paper's red, the magnets' red
  and blue).
- `img/`: PNG images used by the decks (figure crops from the paper, frames of
  our runs).
- `exports/YYYY-MM-DD/`: the PDFs shown at each meeting, versioned.

Render a deck (Node.js and Google Chrome needed), from the repo root:

```bash
npx -y @marp-team/marp-cli@4.5.1 --no-stdin --theme-set slides/theme --html --allow-local-files \
    slides/1-context.md --pdf -o runs/slides-preview/1-context.pdf
```

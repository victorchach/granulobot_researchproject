# Meeting slides

Slides for the regular meetings with the supervisor, written with
[Marp](https://marp.app/) (Markdown to PDF, PPTX or HTML). There is one deck
per theme:

| Deck | Theme |
| --- | --- |
| [`1-context.md`](1-context.md) | Granulobots, the assignment, goal, roadmap |
| [`2-model.md`](2-model.md) | the physical model and where its numbers come from |
| [`3-architecture.md`](3-architecture.md) | code architecture, version by version, and the workflow |
| [`4-results.md`](4-results.md) | results, in the order of [`results/journal.md`](../results/journal.md) |

Slides are only added, never replaced: a new architecture or model gets a new
slide after the old one, so the decks tell how the project evolved. Each slide
says in its footer when it was added. The `slides` skill
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

---
name: slides
description: Use to update the meeting slides in slides/ (Marp decks, one per theme) when something worth presenting happens, or to prepare a meeting with the supervisor. Examples of requests: "add this to the slides", "put the new architecture in the deck", "prépare la réu de jeudi", "export the slides for the meeting", "mets ce résultat dans le diapo". Also offered by keep-result after a run is kept, and by feature after a merge that changes the model or the architecture.
---

# Update the meeting slides

The slides present the project to the supervisor at regular meetings. They
are four Marp decks, one per theme, in `slides/`:

| Deck | Theme | Main source |
| --- | --- | --- |
| `1-context.md` | Granulobots, the assignment, goal, roadmap | `references/`, `docs/roadmap.md` |
| `2-model.md` | the physical model and where the numbers come from | `docs/model.md`, `src/granulobot/parameters.py` |
| `3-architecture.md` | code architecture, its versions, the workflow | `docs/architecture.md`, `specs/`, `AGENTS.md` |
| `4-results.md` | results, in the order of the journal | `results/journal.md`, `results/*/README.md` |

The slides are a view of the repo's sources of truth, not a new one. Take
every fact from those files (or from a run's JSON and CSV) and never put a
number on a slide that the sources do not contain. "The developer" is the
person you work with; talk to them in their language. The slides are in
English, like everything in the repo.

## Rules

- **Add, never replace.** When something changes (a new architecture, a
  revised model), add a new slide after the old one and say what changed and
  why. Keep the old slide: the decks tell how the project evolved. Mark
  versions with a tag in the title, for example
  `## <span class="tag">v3</span> ...`. Fix a slide in place only for an error.
- **Every slide carries its date** in its footer:
  `<!-- _footer: "Added YYYY-MM-DD" -->`, plus its source when useful
  (`· journal entry 3 · results/...`). That is how a meeting finds what is new.
- **Results follow the journal**: one slide per journal entry, in the same
  order and with the same numbers, plus a slide for a key explanation when
  it helps.
- **One line per bullet in the source.** Marp turns every line break inside
  a paragraph or bullet into a visible break, so never wrap a bullet over
  several lines.
- Keep slides short: a title, an image or a code block, three or four
  bullets. If a slide overflows its footer, cut text or shrink the image
  (`![w:700](img/...)`).
- Images go in `slides/img/` as PNG (frames extracted from a GIF, figure
  crops). GIF files stay in `results/`; the pre-commit hook refuses them
  elsewhere. Cite the source of any figure taken from a paper under the
  slide (`<div class="note">...</div>`).
- The theme is `slides/theme/granulobot.css`. Classes: `title` (deck cover),
  `divider`, `cols` and `cols-wide-left` (two columns), `note`, `tag`
  (`tag blue`, `tag grey`).

## 1. Add or update slides

1. Find what changed since the slides were last updated: the footers'
   dates, `git log` since then, new entries in `results/journal.md`, new
   entries in `docs/decisions.md`, merged specs in `specs/README.md`.
2. Pick the deck for each item and write the slide, following the rules
   above. Update the roadmap slide in `1-context.md` when a step's status
   changes.
3. Render and look at the result before showing it (see Commands). Check
   for overflow, broken lines and unreadable images.
4. Show the developer the new slides (paths and a short summary). Suggest a
   commit; commit only when asked.

## 2. Prepare a meeting

1. Update the decks as in section 1.
2. List the slides added since the previous export (compare footer dates with
   the latest folder in `slides/exports/`). That list is the meeting's "what
   is new"; ask the developer which decks to present.
3. Export the PDFs into `slides/exports/YYYY-MM-DD/` (the meeting date).
   These dated exports are versioned: they record what was shown.
4. Suggest a commit.

## Commands

Marp CLI needs Node.js and Google Chrome (or Chromium). From the repo root:

```bash
# Preview: PNG of every slide, into runs/ (ignored by git)
npx -y @marp-team/marp-cli@4.5.1 --no-stdin --theme-set slides/theme --html --allow-local-files \
    slides/4-results.md --images png -o runs/slides-preview/4-results.png

# Meeting export: one PDF per deck
npx -y @marp-team/marp-cli@4.5.1 --no-stdin --theme-set slides/theme --html --allow-local-files \
    slides/4-results.md --pdf -o slides/exports/YYYY-MM-DD/4-results.pdf

# PowerPoint: each slide as an image (faithful, not editable)
npx -y @marp-team/marp-cli@4.5.1 --no-stdin --theme-set slides/theme --html --allow-local-files \
    slides/4-results.md --pptx -o runs/slides-preview/4-results.pptx

# PowerPoint with editable text (experimental, needs LibreOffice; layout may shift)
npx -y @marp-team/marp-cli@4.5.1 --no-stdin --theme-set slides/theme --html --allow-local-files \
    slides/4-results.md --pptx --pptx-editable -o runs/slides-preview/4-results-editable.pptx
```

In VS Code, the Marp for VS Code extension (recommended in
`.vscode/extensions.json`, configured in `.vscode/settings.json`) shows a live
preview with the project theme: open a deck and click the preview button
(Cmd+K V). Its "Export slide deck" command also gives PDF, PPTX or HTML.
The source of truth stays the Markdown: edits made in an exported PPTX are
not carried back.

`--allow-local-files` lets Chrome read the images in `slides/img/`; Marp
warns about it, which is expected.

## Final checks

- [ ] Every new slide has an "Added YYYY-MM-DD" footer and its facts come from the repo's sources
- [ ] No old slide was replaced; changes are new slides with a version tag
- [ ] The rendered slides do not overflow and have no broken lines
- [ ] Results slides match `results/journal.md`
- [ ] Nothing committed or pushed without the developer's approval

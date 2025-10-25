_Related: [Glossary](GLOSSARY.md) • [Architecture overview](architecture/ArchitectureOverview.md) • [Methodology: AI assistant methodology](methodology/AI-Assistant-Methodology.md)_

# Documentation style guide

This style guide applies to all docs under `docs/`.

## Voice

- Declarative.
- Direct.
- Operational, not marketing.

Bad: "RetroVue is an innovative platform that empowers..."
Good: "RetroVue turns scheduled content into a live Channel stream when someone tunes in."

## Headers

- Use sentence case.
- `## Purpose`, not `## PURPOSE` and not `## System Overview`.

## Structure

Domain docs should follow this section order:

1. Purpose
2. Core model / scope
3. Contract / interface
4. Execution model
5. Failure / fallback behavior
6. Operator workflows (if relevant)
7. Naming rules

Runtime docs should follow the same order unless it doesn't apply.

## Terminology

Use these exact words:

- Channel
- ChannelManager
- Producer
- Producer Registry
- Enricher (never "enhancer", never "overlay stage")
- playout plan
- AssetDraft
- Playlog / as-run log / EPG
- MasterClock

## Formatting rules

- Short paragraphs.
- Bullet lists are preferred for examples.
- No filler like "basically", "of course", "obviously".
- No future tense promises unless in a "Future expansion" section.

## Cross-links

- Each doc should have a `See also:` section at the bottom linking to the most related docs.
- Each doc should begin with a one-line `_Related: ..._` breadcrumb block that links to closest neighbors.

See also:

- [Glossary](GLOSSARY.md)
- [Architecture overview](architecture/ArchitectureOverview.md)

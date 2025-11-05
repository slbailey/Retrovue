# Runtime — Rule Parsers

_Related: [Channel Manager](../ChannelManager.md) • [Schedule Template](../../domain/ScheduleTemplate.md) • [Schedule Day](../../domain/ScheduleDay.md)_

## Purpose

This directory contains **rule parsers** used by the runtime to interpret and apply domain logic at execution time. Rule parsers operate on persisted domain models (such as `ScheduleTemplateBlock`) but are _not_ themselves part of the canonical domain model. Instead, they provide the logic needed to convert static programming rules and templates into actionable scheduling or playout instructions.

## What is a Rule Parser?

Rule parsers are responsible for turning configuration or templates into runtime selections or actions. They typically answer questions like:

- **Which content items should fill a given schedule block?**
- **Which interstitial (e.g., promo, bumper, ad) should be used to pad or fill a gap in the playout?**
- **How should blocks and transitions be populated during runtime based on assigned rules?**

## Example Uses

- **Filling a ScheduleTemplateBlock:** For a template block like "Afternoon Sitcoms," a rule parser determines which sitcoms from an eligible pool should be scheduled into that block.
- **Selecting Interstitials for Ad Blocks:** When the schedule engine encounters an ad or interstitial block, a rule parser can select the most appropriate promo/bumper from a pool according to configured rules (e.g., "rotate evenly", "avoid repeats", "must match channel branding").

## Relationship to Domain and Runtime

- Rule parsers **interpret** domain model assignments and configurations, but do not define the domain structure.
- They are _runtime logic_ that sits between static data (templates, assignments) and the live execution engine.
- They should not depend on runtime state outside the provided inputs (i.e., should be pure functions or clearly documented if not).

## Not Domain Models

Unlike entities defined in `src/retrovue/domain/entities.py` (see [ScheduleDay](../../domain/ScheduleDay.md)), rule parsers do not persist data or participate in ORM mappings. They operate **on** domain objects, translating rules into runtime actions.

## See Also

- [ChannelManager](../ChannelManager.md): How schedules and rules are applied during streaming.
- [ScheduleTemplate](../../domain/ScheduleTemplate.md): Persistent templates defining programming blocks.
- [Operator CLI](../../operator/CLI.md): Assigning and managing programming rules.

---

For implementation guidelines and extension strategies, see [Architecture Overview](../../architecture/ArchitectureOverview.md).

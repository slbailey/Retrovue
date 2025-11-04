# Contract — ScheduleTemplate Binding v0.1

## Scope

Binding rules between templates and a channel; integrity of dayparts and slots.

## Rules (numbered)

1. Channel required: Every template has a valid `channel_id` referencing an existing Channel.
2. Single effective template: At any wall-clock instant, ≤1 active/effective template per channel (consider date windows).
3. Daypart integrity: Dayparts in a single template do not overlap; if full-day coverage is declared, they cover `[00:00,24:00)` in channel timezone. If not declaring full-day coverage, uncovered spans are allowed.
4. Block alignment: Each `duration_blocks` is an integer ≥1 and aligns to the channel’s `grid_block_minutes`.
5. Underfill explicit: Underfill is permitted only if `allow_underfill=true`; otherwise slot content must meet or exceed block duration (enforced by playlog builder).
6. Versioning: Material changes to `daypart_rules` or `block_slots` require `version++`.
7. Timezone authority: All template interpretation uses the channel’s timezone and `programming_day_start`.

## Required tests

- `tests/contracts/domain/test_schedule_template_binding.py::test_template_requires_valid_channel_id`
- `tests/contracts/domain/test_schedule_template_binding.py::test_single_effective_template_per_channel`
- `tests/contracts/domain/test_schedule_template_binding.py::test_dayparts_do_not_overlap_and_cover_declared_span`
- `tests/contracts/domain/test_schedule_template_binding.py::test_block_slots_align_to_channel_grid_block_minutes`
- `tests/contracts/domain/test_schedule_template_binding.py::test_underfill_only_when_explicitly_allowed`
- `tests/contracts/domain/test_schedule_template_binding.py::test_version_bumps_on_material_change`
- `tests/contracts/domain/test_schedule_template_binding.py::test_template_interpretation_uses_channel_timezone_and_day_anchor`

## Out of scope

Program selection, ad pod design, overlay policy.



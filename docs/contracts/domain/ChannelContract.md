# Contract — Channel v0.1

## Scope

Canonical Channel invariants needed for schedule templates and horizon building.

## Rules (numbered)

1. Slug uniqueness & immutability: `slug` is lowercase kebab-case, unique, and immutable after creation.
2. Timezone validity: `timezone` must be a valid IANA identifier; all template/daypart math uses the channel’s timezone.
3. Grid atom: `grid_block_minutes ∈ {15,30,60}` in v0.1.
4. Offsets domain: `block_start_offsets_minutes` is non-empty; values are integers in `[0,59]`, sorted and unique.
5. Offset/grid alignment: Let gaps be differences between consecutive offsets wrapping to 60. `gcd(gaps) == grid_block_minutes`. Example: offsets `[:05,:35]` pass for 30; `[0,15,30,45]` passes for 15.
6. Programming day anchor: `programming_day_start` is a valid `HH:MM:SS`; daypart spans are anchored to this time (DST-aware).
7. Activation semantics: Only `is_active=true` channels are considered by horizon builders.
8. Deletion safety: Channels with attached templates/schedules are not hard-deleted; prefer archival (`is_active=false`).
9. Kind is descriptive (v0.1): `kind ∈ {network,premium,specialty}`; `kind` must not drive runtime behavior in v0.1.

## Required tests

- `tests/contracts/domain/test_channel_contract.py::test_slug_unique_and_immutable`
- `tests/contracts/domain/test_channel_contract.py::test_timezone_is_valid_iana`
- `tests/contracts/domain/test_channel_contract.py::test_grid_block_minutes_allowed_values`
- `tests/contracts/domain/test_channel_contract.py::test_offsets_sorted_unique_and_in_range`
- `tests/contracts/domain/test_channel_contract.py::test_offsets_gcd_equals_grid_block_minutes`
- `tests/contracts/domain/test_channel_contract.py::test_programming_day_start_valid_time_and_dst_anchor`
- `tests/contracts/domain/test_channel_contract.py::test_inactive_channels_excluded_from_horizon`
- `tests/contracts/domain/test_channel_contract.py::test_cannot_delete_channel_with_dependencies_archive_instead`
- `tests/contracts/domain/test_channel_contract.py::test_kind_enum_nonfunctional_in_v0_1`

## Out of scope

Branding/overlays, ad policies, guide playout, viewer fanout.



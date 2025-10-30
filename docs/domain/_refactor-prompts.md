# PROMPT 1

You are rewriting `docs/domain/Asset.md` to align with RetroVue's current domain documentation standard.

AUTHORITATIVE INPUTS:

1. `docs/domain/README.md` – This defines the structure, style, and voice for all domain docs. Treat this as the spec.
2. `docs/domain/Collection.md` – Use this as the template for tone, depth, formatting, and cross-references.
3. The CURRENT contents of `docs/domain/Asset.md` – This is legacy. It may have wording and concepts that predate our contract/test-first discipline. We do NOT want to lose any correct detail here, even if it needs to be reframed.

GOAL:
Produce a brand new `docs/domain/Asset.md` that:

- Uses the exact section ordering and style defined in README.md and demonstrated in Collection.md.
- Keeps all meaningful semantics from the legacy Asset.md, but updates them to match current language, relationships, invariants, and lifecycle rules.
- Removes any contradictions with newer rules.
- Adds any missing required sections so that Asset.md "looks like" Collection.md in terms of headings and depth.

OUTPUT RULES:

1. Start file with the header:
   `# Domain — Asset`
   and then a short Related line like:
   `Related: [Collection](Collection.md) • [Source](Source.md) • [Scheduling](Scheduling.md) • [Ingest Pipeline](IngestPipeline.md) • [Contracts](../contracts/README.md)`
   (Update the related list if needed to reflect Asset’s real neighbors.)

2. Your rewritten doc MUST include (in this order unless otherwise noted):

   - Purpose
   - Core model / scope
     - Primary key / identity fields
     - Required fields
     - Lifecycle / state fields
     - Technical metadata fields
     - Relationships
     - Indexes (if relevant)
   - Contract / interface
     - Lifecycle states
     - Critical invariants
     - Allowed transitions and rules (what can and can’t happen)
     - Duplicate / change detection behavior
   - Contract-driven behavior
     - How CLI noun-verb pairs map to Asset operations
     - Safety expectations
     - Testability expectations
     - Idempotence / transaction boundaries
   - Execution model
     - How Assets flow through ingest → enrichment → approval → scheduling → playout
     - Which services operate on Asset
     - Which parts of the system are allowed to see/use which states
   - Failure / fallback behavior
     - What happens when ingest or enrichment breaks
     - Safety rules for delete/restore, especially around scheduled content
   - Operator workflows
     - Discovery / ingest
     - Selection / filtering / targeting assets
     - Approval / broadcast readiness
     - Cleanup / retirement
   - Naming rules
     - Canonical casing (Asset vs assets)
     - Table naming
     - CLI naming
     - UUID spine rule
   - See also
     - Cross-links to other domain docs

3. Treat Asset as a SINGLE canonical entity with lifecycle states (`new`, `enriching`, `ready`, `retired`) and approval gates. Do NOT imply there are “ingest assets” and “broadcast assets” as separate models. There is only Asset with states. This is already described in the current Asset.md; keep/reinforce it.

4. Keep and restate these invariants clearly and boldly:

   - An Asset in `ready` MUST have `approved_for_broadcast=true`.
   - An Asset with `approved_for_broadcast=true` MUST be in `ready`.
   - Scheduling and playout may ONLY operate on Assets in `ready` with `approved_for_broadcast=true`.
   - Assets MUST belong to exactly one Collection via `collection_uuid`.
   - Newly discovered content MUST enter as `new` or `enriching`, never directly `ready`.

5. Preserve all important technical details from the legacy Asset.md, including:

   - The fact that `uuid` is the spine for all asset-related tables and downstream references.
   - Field-level notes like `uri`, `duration_ms`, `hash_sha256`, codecs, etc.
   - Relationship notes (ProviderRef, Marker, ReviewQueue, Episode via many-to-many, etc.).
   - Index strategy (`canonical`, `state`, `approved_for_broadcast`, etc.).
   - Change detection rules (content hash changes, enricher config changes).
   - Contract-driven safety (test DB, dry run, transactional integrity, cannot hard-delete assets referenced by playout logs in production, etc.).
   - Operator CLI flows (`retrovue assets select`, `retrovue assets delete`, etc.).

6. Where legacy text conflicts with Collection.md or README.md:

   - Defer to README.md and Collection.md tone, formatting, and philosophy.
   - Update wording to reflect contract-first, test-backed operations and operator mental model.
   - Update “ingest pipeline” wording so it matches Collection.md language about Source → Collection → Asset hierarchy and progressive enrichment.

7. DO NOT invent fields or behaviors not present in either:

   - the legacy Asset.md,
   - Collection.md,
   - or README.md.
     It’s okay to reorganize or rephrase, but do not add new capabilities that aren’t documented.

8. Use the same heading levels and markdown style as Collection.md:

   - `## Purpose`
   - `## Core model / scope`
   - etc.
     Subsections inside can use `###`.

9. The final output should completely replace the current contents of `docs/domain/Asset.md`. Do not include any explanation text to me; just output the final markdown of the file.

Now rewrite `docs/domain/Asset.md` accordingly.

# Prompt 2

Review the current `docs/domain/Asset.md` I just generated.

Check only for these issues:

1. SECTION ORDER MATCH:
   The sections should appear in this order:

   - Purpose
   - Core model / scope
   - Contract / interface
   - Contract-driven behavior
   - Execution model
   - Failure / fallback behavior
   - Operator workflows
   - Naming rules
   - See also

   Fix the order if it's wrong. Do not rename the sections unless the naming in README.md or Collection.md uses a different exact heading.

2. LANGUAGE TONE MATCH:
   The voice, formatting, and level of detail should match `docs/domain/Collection.md`:

   - Short, direct, operator-aware.
   - Uses MUST / ONLY / NEVER for invariants.
   - Uses bullet lists and code blocks where appropriate.
   - Avoids “storytelling” or speculative language.

   Update the wording to match that tone.

3. INVARIANTS:
   Confirm these show up, clearly and unambiguously:

   - Asset in `ready` MUST have `approved_for_broadcast=true`.
   - `approved_for_broadcast=true` MUST imply `ready`.
   - Only `ready` + `approved_for_broadcast=true` is eligible for scheduling and playout.
   - Asset MUST belong to exactly one Collection.
   - Assets enter as `new` or `enriching`, never directly `ready`.

   If any are missing or fuzzy, strengthen them.

4. TABLE / FIELD DEFINITIONS:
   Make sure all of the important fields from the legacy Asset.md made it in:

   - uuid
   - uri
   - size
   - state
   - canonical
   - collection_uuid
   - approved_for_broadcast
   - duration_ms
   - codecs/container
   - hash_sha256
   - discovered_at / is_deleted / deleted_at
   - relationships (ProviderRef, Marker, ReviewQueue, Episode link)
   - indexes (canonical, state, approved_for_broadcast, discovered_at, is_deleted, collection_uuid)

   If any of those are missing, add them back in under “Core model / scope”.

5. SAFETY / CONTRACTS:
   Verify that we clearly document:

   - asset operations are driven by noun-verb CLI contracts like `retrovue assets select`, `retrovue assets delete`, etc.
   - destructive operations require explicit confirmation / flags.
   - production safety rules around deleting assets referenced by playout history.
   - `--test-db`, `--dry-run`, and transactional isolation.

   If anything is missing, add it back to “Contract-driven behavior” or “Failure / fallback behavior”, whichever is more appropriate.

When you're done, output the corrected final markdown for `docs/domain/Asset.md` with no other commentary.

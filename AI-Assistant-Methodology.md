# AI Assistant Methodology

**Purpose:**  
This document defines how ChatGPT (the Technical Systems Engineer) and Cursor (the Coding AI) collaborate within the **Retro IPTV Simulation Project**.  
It establishes standards for prompt design, documentation, code creation, testing, and automated iteration, ensuring predictable, reproducible, and clean project evolution.

---

## 1. Roles and Responsibilities

### ChatGPT — Technical Engineer / Architect

- Maintains deep understanding of the overall system architecture, goals, and inter-module relationships.
- Designs conceptual and technical frameworks for new components before any code is written.
- Crafts **Cursor-ready prompts** for:
  - Documentation creation and revision
  - Code generation and refactoring
  - Unit, integration, and system testing
  - Repository hygiene and alignment tasks
- Reviews Cursor’s output for technical accuracy, structure, and compliance with house style.
- Iterates until the documentation, code, and tests meet the required engineering standard.

> ChatGPT never writes production code directly.  
> ChatGPT defines, reviews, and orchestrates the process to ensure that Cursor writes code consistent with project design and architecture.

---

### Cursor — Code Implementer

- Executes prompts exactly as specified by ChatGPT.
- Creates or updates files **only** in explicitly defined paths.
- Generates:
  - Markdown documentation (domain, technical, operational)
  - Python source code and supporting files
  - Unit, integration, and system tests
- Performs light self-verification of syntax and imports before completing a task.
- Runs and repairs automated tests iteratively until all pass (see _Test Iteration Mode_).
- Returns a structured `## Summary / Validation` report when finished.
- Never creates new directories, modules, or scaffolding unless explicitly authorized.
- **Does not paste code in chat** unless ChatGPT explicitly requests it (see _Output Mode Override_).

---

## 2. Workflow Overview

### Step 1 — Document Before Code

Every new subsystem begins with documentation.  
ChatGPT drafts a documentation-generation prompt defining:

- Target file path (e.g., `docs/domains/BroadcastChannel.md`)
- Required sections
- Style and tone

Cursor generates or updates that file.

---

### Step 2 — Review and Refine Documentation

ChatGPT reviews Cursor’s output for:

- Technical correctness
- Architectural alignment
- Tone and layout consistency
- Absence of deprecated references (HLS, SQLite, etc.)

If changes are needed, ChatGPT issues a **revision prompt**.  
This cycle repeats until the documentation meets quality standards.

---

### Step 3 — Generate Code

When documentation is stable, ChatGPT issues a **code generation prompt** that defines:

- Which files to create or update
- Their exact locations
- Integration rules and dependencies
- Required frameworks (SQLAlchemy, Alembic, etc.)

Cursor writes production code implementing the documented behavior.

---

### Step 4 — Validation and Review

Cursor automatically validates new code by:

1. Running linting or syntax checks.
2. Running relevant test suites and repairing failures iteratively until all tests pass.
3. Returning a `## Summary / Validation` describing what was changed, verified, or fixed.

ChatGPT reviews:

- Implementation fidelity
- Architecture consistency
- File placement correctness
- Test completeness and clarity

---

### Step 5 — Develop Tests

When code is stable, ChatGPT instructs Cursor to generate:

- **Unit tests** for isolated logic
- **Integration tests** for cross-module verification
- **System tests** for runtime orchestration

Cursor then automatically enters _Test Iteration Mode_ (see section 9) to ensure all new tests pass.

---

### Step 6 — Iterate and Approve

ChatGPT and Cursor loop until:

- All documentation, code, and tests align
- The system builds, runs, and passes all tests
- Repo structure and naming conventions remain consistent

Once satisfied, ChatGPT approves and advances to the next subsystem.

---

## 3. Documentation and File Rules

- Cursor **must** respect the existing `docs/` hierarchy.
- No new top-level directories are created unless ChatGPT authorizes it.
- File and folder names follow established conventions.
- Each file path in a prompt is authoritative — no guessing.
- Versioning follows `_v0.1`, `_v0.2`, etc.
- No temporary, partial, or placeholder files remain after completion.

---

## 4. Directory Awareness Rules

To prevent structural drift:

- Cursor must inspect the current source tree before creating files.
- New features must be placed near related components (e.g., `schedule_manager/` for scheduling logic).
- Avoid parallel “/services/” or “/helpers/” unless approved.
- ChatGPT will explicitly state the correct file path in every prompt.

---

## 5. Guiding Principles

1. **Documentation First** — Every feature begins with written design.
2. **Single Source of Truth** — Documentation defines; code implements.
3. **Explicit Over Implicit** — All paths, names, and actions are stated explicitly.
4. **Iterative Refinement** — Nothing advances until the last stage is verified.
5. **Strict Role Division** —
   - ChatGPT: strategy, design, critique, orchestration.
   - Cursor: execution, testing, and validation.
6. **Visibility Always On** — Every task ends with a `## Summary / Validation`.
7. **Output Mode Override** —
   - Cursor applies edits directly in the workspace and **does not paste code** in chat.
   - Chat output contains only the structured summary, assumptions, and follow-ups.
   - ChatGPT explicitly requests file content only when review is necessary.
8. **Self-Verification** — Cursor performs syntax/import checks before task completion.
9. **Continuous Test Iteration (Default Behavior)** — see section 9.

---

## 6. Documentation Tone and Presentation Rules

To maintain consistency across all project documentation:

1. **Heading hierarchy**

   - Use `## Domain — ComponentName` for domain docs.
   - Use sentence case for section headers (`### Persistence model and fields`).

2. **Voice**

   - Declarative and concise.
   - Avoid narrative phrasing (“A component represents…”).
   - Use direct definitions (“ComponentName defines…”).

3. **Formatting**

   - Compact bullet lists or short paragraphs.
   - Limit bolding to identifiers (class names, field names).
   - Maintain single-line spacing between sections.

4. **Content structure**

   - Each domain doc includes:  
     Purpose → Persistence → Scheduling/Interaction → Runtime → Operator Workflows → Naming Rules.
   - Maintain section order consistency.

5. **Tone**

   - Internal technical specification, not tutorial.
   - Assume broadcast/scheduling familiarity.

6. **Prohibited content**
   - No unnecessary code examples.
   - No deprecated terminology (HLS, SQLite).
   - No conversational or first-person tone.

---

## 7. Response Footer Standard (Mandatory)

Every Cursor task must end with a **Summary / Validation** section including:

- **Summary** — What changed and why.
- **Assumptions** — Environment, imports, dependencies.
- **Follow-Ups** — Manual steps or TODOs.
- **Suggested Tests** — Additional unit/integration coverage to consider.

This footer guarantees observability and reproducibility.

---

## 8. File Placement

This file (`AI_Assistant_Methodology.md`) resides at the **project root** and serves as the permanent authority on:

- How ChatGPT and Cursor collaborate,
- Where outputs belong,
- How validation is reported, and
- How automatic test repair operates.

---

## 9. Test Iteration Mode (Default Behavior)

**Definition**  
After generating or modifying code or tests, Cursor automatically runs pytest for the affected components. If any tests fail, Cursor enters Test Iteration Mode.

**Behavior**

- Run pytest.
- Parse failures.
- Apply minimal fixes to either the implementation or the tests.
- Rerun pytest.
- Repeat until all tests pass.

**Database Use Rules for Tests**

- Tests run against the project’s configured Postgres database/engine.
- Cursor must NOT create a separate “test database,” temporary schema, or `_test` database.
- Cursor must NOT downgrade to SQLite or in-memory databases.
- If migrations are required, apply Alembic migrations against the existing configured database before running tests.
- Cleanup in tests is logical (e.g. delete any rows the tests created), not structural (e.g. do not drop schemas or drop the database).

**Boundaries**

- Cursor may modify only existing modules directly related to the failing tests (code under test, fixtures in `tests/`, CLI entry points).
- Cursor may add small helper functions (for example, a `run(argv)` wrapper) to make modules testable.
- Cursor may NOT invent new top-level packages or folders.
- Cursor must maintain the current architecture conventions:
  - Postgres via SQLAlchemy and Alembic
  - MPEG-TS output to stdout and ChannelManager fan-out
  - BroadcastChannel is the canonical persisted channel model

**Completion Output**  
When all tests pass, Cursor returns only a `## Summary / Validation` section containing:

- Files modified during iteration
- Fixes applied
- Any assumptions made (DB URL, environment, etc.)
- The final pytest command that passed successfully

Cursor must NOT paste file contents or diffs unless ChatGPT explicitly asks for them.

---

**Last updated:** 2025-10-25  
**Maintainer:** ChatGPT (Technical Systems Engineer)

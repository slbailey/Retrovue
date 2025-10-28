# Development Standards

This document defines the quality gates and cultural principles for the Retrovue project.

## Runtime Standard

- **Python 3.12+** - All code must run on Python 3.12 or later

## Behavior Standard

- **All CLI behavior is defined by contract docs in `docs/contracts/`** - CLI interfaces are contractually specified, not ad-hoc

## Cross-Domain Boundaries

- **Defined in `docs/contracts/resources/cross-domain/`** - Inter-module interactions follow documented boundaries

## Enforcement Standard

The following commands **must exit 0** for any code to be merged:

- `ruff check .` - Code style and quality
- `mypy src/ --ignore-missing-imports` - Type safety
- `pytest tests/contracts` - Contract compliance

**CI will block any PR that violates any of the above.**

## Contract-Driven Development

**You may not "fix the tests" by changing a contract test unless you're also updating the related contract doc and `CONTRACT_MIGRATION.md`**

This is the core cultural principle: **tests don't drift silently; contracts drive tests, tests drive code.**

When behavior needs to change:

1. Update the contract documentation first
2. Document the change in `CONTRACT_MIGRATION.md`
3. Update the contract tests to match the new contract
4. Update the implementation code to pass the new tests

This ensures that all behavior changes are intentional, documented, and traceable.

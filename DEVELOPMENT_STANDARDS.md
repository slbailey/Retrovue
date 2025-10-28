# Development Standards

- Python: 3.12 is the reference interpreter.
- CI runs pytest, mypy, and ruff under Python 3.12.
- All code must type-check under mypy, lint cleanly under ruff, and satisfy all contract tests.
- Behavior must match the contract documents in `docs/contracts/` and cross-domain guarantees in `docs/contracts/resources/cross-domain/`.

Pull requests that pass unit tests but fail mypy/ruff will not be merged.

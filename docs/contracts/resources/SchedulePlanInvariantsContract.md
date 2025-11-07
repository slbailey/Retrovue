# Schedule Plan Invariants Contract

**Moved:** See [Scheduling Invariants](SchedulingInvariants.md).

**Key Invariant:** All SchedulePlans must satisfy **INV_PLAN_MUST_HAVE_FULL_COVERAGE** (S-INV-14), requiring full 24-hour coverage (00:00–24:00) with no gaps. Plans are automatically initialized with a default "test pattern" zone if no zones are provided. See [Scheduling Invariants](SchedulingInvariants.md#s-inv-14-plan-must-have-full-coverage-inv_plan_must_have_full_coverage) for details.
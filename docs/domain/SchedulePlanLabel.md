_Related: [Architecture](../architecture/ArchitectureOverview.md) • [SchedulePlan](SchedulePlan.md) • [ScheduleDay](ScheduleDay.md) • [Operator CLI](../operator/CLI.md)_

# Domain — SchedulePlanLabel

## Purpose

SchedulePlanLabel is for organizing and annotating blocks within a [SchedulePlan](SchedulePlan.md). Labels provide visual organization and grouping of related block assignments, such as "Morning Cartoons" or "Primetime Movie." These are **purely visual/organizational** and **not enforceable by the scheduler** — they have no impact on scheduling execution or logic.

Labels can span multiple block assignments, allowing operators to group related content together for better organization and visualization. The same label can be applied to multiple assignments within a plan, and labels can be reused across different schedule plans.

**Critical Rule:** Labels are purely visual/organizational and are not enforced or used by the scheduler. They exist solely to help operators organize and annotate blocks within schedule plans.

## Core Model / Scope

SchedulePlanLabel enables:

- **Organizing and annotating blocks** within a SchedulePlan
- **Visual grouping** of related block assignments (e.g., "Morning Cartoons", "Primetime Movie", "Late Night Movies")
- **Improved workflow and plan readability** through visual organization
- **Optional categorization** without affecting scheduling behavior
- **Spanning multiple block assignments** — a single label can be applied to multiple assignments within a plan
- **Reusability** across different schedule plans

**Key Points:**
- Labels are for organizing and annotating blocks within a SchedulePlan
- Labels are **purely visual/organizational** and **not enforceable by the scheduler**
- Labels can span multiple block assignments, allowing grouping of related content
- Labels do not affect scheduling logic, execution, or validation
- Labels can be reused across different schedule plans
- Multiple blocks can share the same label for visual grouping
- Examples: "Morning Cartoons", "Primetime Movie", "Late Night Movies", "News Hour"

## Contract / Interface

SchedulePlanLabel is an organizational concept with the following characteristics:

- **Label identity**: Unique identifier for the label (UUID)
- **Label name** (String): The operator-defined label name (e.g., "Morning Cartoons", "Primetime Movie", "Late Night Movies")
- **Block association**: Labels can be associated with one or more [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) entries via the `label_id` field, allowing labels to span multiple block assignments
- **Purely visual/organizational**: Labels are not enforceable by the scheduler and have no impact on scheduling logic
- **Optional**: Labels are not required for any scheduling functionality

**Examples:**
- "Morning Cartoons" - organizes and annotates early morning children's programming blocks
- "Primetime Movie" - organizes and annotates evening movie blocks
- "Late Night Movies" - organizes and annotates late evening movie blocks
- "News Hour" - organizes and annotates news programming blocks

## Execution Model

**No Execution Impact:** SchedulePlanLabel has no impact on scheduling execution. The scheduler does not read, validate, or use labels in any way. Labels are **purely visual/organizational** and **not enforceable by the scheduler**.

**Visual Organization Only:** Labels are used for organizing and annotating blocks within a SchedulePlan. They may be:
- Displayed alongside or above grouped blocks in plan editors
- Used for filtering or organizing blocks in the UI
- Shown in schedule previews or visualizations
- Used for operator workflow convenience and plan readability

**Persistence:** Labels are persisted in the database but are not used by the scheduler. They are:
- Stored as separate entities that can be referenced by block assignments
- Referenced via `label_id` in SchedulePlanBlockAssignment entries
- Not included in scheduling logic or validation
- Not part of the scheduling execution model

## Relationship to SchedulePlanBlockAssignment

Labels can optionally be associated with [SchedulePlanBlockAssignment](SchedulePlanBlockAssignment.md) entries via the `label_id` field for visual grouping and annotation. This association:

- **Allows labels to span multiple block assignments** — a single label can be applied to multiple assignments within a plan
- Does not affect the assignment's scheduling behavior
- Does not enforce any constraints or rules
- Is purely visual/organizational and not enforceable by the scheduler

**Example:** Multiple assignments with start_time "06:00", "06:30", "07:00" might all share the same `label_id` referencing a "Morning Cartoons" label, creating a visual group of related morning programming blocks. The same label can be reused across different schedule plans, allowing operators to maintain consistent organizational patterns across multiple plans.

## Operator Workflows

**Create Labels**: Operators can create labels for organizing and annotating blocks within schedule plans (e.g., "Morning Cartoons", "Primetime Movie").

**Apply Labels to Blocks**: Operators can optionally apply labels to block assignments when creating or editing schedule plans. A single label can span multiple block assignments, allowing grouping of related content.

**Group Related Blocks**: Use labels to visually group blocks that share a theme, daypart, or content type (e.g., all morning programming, all movie blocks). Labels help operators quickly identify and organize blocks in complex plans with many assignments.

**Visual Organization**: Labels help operators quickly identify and organize blocks in complex plans with many assignments, improving workflow and plan readability.

**No Scheduling Impact**: Operators should understand that labels are **purely visual/organizational** and **not enforceable by the scheduler** — they do not affect what actually airs or when it airs.

## Guidance for Implementation

**Do Not:**
- Use labels in scheduling logic or validation
- Require labels for plan creation or execution
- Enforce any rules based on labels
- Allow labels to affect scheduling behavior
- Make labels enforceable by the scheduler

**Do:**
- Keep labels as purely visual/organizational elements
- Allow operators to optionally apply labels for organizing and annotating blocks
- Allow labels to span multiple block assignments within a plan
- Display labels in plan editors and visualizations
- Make labels easily editable and removable
- Clearly communicate that labels are purely visual/organizational and not enforceable by the scheduler

**Best Practices:**
- Labels should be short and descriptive (e.g., "Morning Cartoons", "Primetime Movie")
- Common labels might include dayparts (Morning, Afternoon, Evening, Late Night) or content types (Movies, Cartoons, News, Sports)
- Labels can span multiple block assignments to group related content
- Operators should not rely on labels for any functional behavior
- UI should clearly indicate that labels are optional, purely visual/organizational, and not enforceable by the scheduler

## Failure / Fallback Behavior

Since labels are purely visual/organizational and not enforceable by the scheduler, there is no failure mode for labels. If labels are missing or invalid:

- Scheduling continues normally (labels are not used in scheduling)
- UI may display blocks without labels
- Operators can reapply labels as needed
- No scheduling impact occurs (labels do not affect what airs or when)

## Naming Rules

The canonical name for this concept in code and documentation is SchedulePlanLabel.

Labels are operator-defined strings with no enforced naming conventions. However, operators may find it useful to use consistent naming patterns (e.g., dayparts, content types) for better organization.

## See Also

- [SchedulePlan](SchedulePlan.md) - Top-level operator-created plans that define channel programming
- [ScheduleDay](ScheduleDay.md) - Resolved schedules for specific channel and date
- [Scheduling](Scheduling.md) - High-level scheduling system
- [Operator CLI](../operator/CLI.md) - Operational procedures

**Note:** SchedulePlanLabel is for organizing and annotating blocks within a SchedulePlan, such as "Morning Cartoons" or "Primetime Movie." These are purely visual/organizational and not enforceable by the scheduler. Labels can span multiple block assignments, allowing operators to group related content together for better organization and visualization. Labels have no impact on scheduling logic, execution, or validation.


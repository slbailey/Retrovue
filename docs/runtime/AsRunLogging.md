_Related: [Runtime: Channel manager](ChannelManager.md) • [Runtime: Master clock](MasterClock.md) • [Operator workflows](../operator/OperatorWorkflows.md)_

# As-run logging

## Purpose

Capture what the Channel actually aired (or attempted to air) over time.

## Core model / scope

- The system records segments, timestamps, enrichments, and transitions as they were scheduled to air and as they actually aired.
- The as-run log exists even if there were zero viewers. The Channel is logically always "on" in schedule terms.

## Contract / interface

The as-run logging layer must be able to answer:

- What was airing on Channel X at timestamp T?
- Did the playout plan include required branding / bugs / warnings?
- Were there failures or fallbacks (e.g. emergency slate instead of intended content)?

## Execution model

- ChannelManager, Producer, and playout enrichment steps emit structured events describing:
  - Channel ID
  - Segment / asset IDs
  - Start/end timestamps from MasterClock
  - Any enrichers applied
  - Any fallback conditions
- These events are appended to a durable store.

## Failure / fallback behavior

- If logging fails, playback must continue. Logging is not allowed to block playout.
- Missing log data should raise an operator-visible warning.

## Naming rules

- "As-run log" is the record of what aired.
- "Playlog" or "playout horizon" is the plan of what is scheduled to air.

See also:

- [Master clock](MasterClock.md)
- [Channel manager](ChannelManager.md)
- [Operator workflows](../operator/OperatorWorkflows.md)

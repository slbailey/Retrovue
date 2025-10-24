# RetroVue UI Design — Schedule Module (Draft v0.1)

> Living document for the Retro IPTV Simulation Project UI. Scope for this draft: schedule template editor, block rule system, and playlog preview. This module provides the core scheduling functionality for creating and managing broadcast schedules.

---

## 1) Goals & Principles

- **Calendar Feel**: Drag from a palette (shows, blocks, movies) into a daily grid. Stretch blocks visually to cover multiple slots.
- **Rule-Driven Blocks**: Each block can represent specific shows or content types (via tags, rating, episode policy).
- **Playlog Visibility**: Hybrid view (grid + linear rundown) shows exactly how episodes and ad pods fill the schedule.
- **Grid Discipline**: Always aligned to 30-min boundaries. Blocks can be 30, 60, 120, or more minutes.
- **Ad Break Accuracy**: Breakpoints come from ingest-time ad_breaks (converted from chapter markers or generated manually).

---

## 2) High-Level UX

### 2.1 Schedule Console (primary view)

- **Header**: Channel selector; "Create Template" / "Load Template" / "Generate Schedule"; Date picker for daily schedules.
- **Palette Panel** (left rail): Draggable content tiles organized by categories (Series, Movies, Blocks).
- **Calendar Grid** (center): 24-hour timeline with 30-minute rows for visual block placement.
- **Block Editor** (right drawer): Rule configuration and content selection for selected blocks.
- **Playlog Preview** (bottom panel): Hybrid view showing grid overview and linear rundown.

### 2.2 Template Manager (supporting view)

- Browse and manage saved schedule templates.
- Template versioning and rollback capabilities.
- Template sharing and import/export functionality.

### 2.3 Schedule Generator (future)

- Automated schedule generation based on templates and rules.
- Conflict detection and resolution.
- Schedule optimization and gap filling.

---

## 3) Integration Strategy

**Template-Driven Architecture:**

- Templates define reusable schedule patterns with rule-based content blocks.
- Daily schedules are generated from templates with date-specific overrides.
- Playlog events are computed from schedules and content metadata.

**Non-goals**: Real-time schedule modification during broadcast; complex multi-channel coordination in v0.1.

---

## 4) UX Design Details

### 4.1 Palette (Left Rail)

- **Categories**: Series, Movies, Blocks, Promos.
- **Draggable tiles**: Visual representations of content (e.g., "Cheers", "Cartoons", "Family Movies").
- **Color-coded by type**: Consistent color scheme across all modules.
- **Search and filter**: Quick access to specific content items.

### 4.2 Calendar Grid (Center Pane)

- **Vertical timeline**: 00:00–24:00 in 30-minute rows.
- **Drag and drop**: Dropping a tile creates a block (30 min default).
- **Stretch handles**: Visual controls to grow blocks to 1h, 2h, 4h, etc.
- **Grid snapping**: No overlaps; blocks automatically snap to 30-minute boundaries.
- **Visual feedback**: Hover states, drop zones, and conflict indicators.

### 4.3 Block Editor (Right Drawer)

- **Basic fields**: Label, Content Type (series|movie|promo|custom), Duration.
- **Rule Builder**:
  - **Series**: Select specific show(s) OR tag(s). Episode policy = syndication|serial|circular.
  - **Movies**: Expression builder (tags + rating combinations).
  - **Promos**: Ad pod configuration and rotation rules.
- **Optional constraints**: Rating guardrails, must-run promos, time restrictions.
- **Preview**: Real-time preview of how the block will be filled (stubbed in v0.1).

### 4.4 Playlog Preview (Bottom Panel)

- **Grid Overview**: Shows all slots/blocks by time with visual indicators.
- **Linear Rundown**: On block expand, shows detailed breakdown:
  - Segment 1 (content)
  - Ad Pod 1 (ads from pool)
  - Segment 2
  - Ad Pod 2 …
- **Timeline details**: Each line shows timestamp, duration, asset ID/title, pool.
- **Padding handling**: Black/padding segments handled at block end (ensures grid alignment).

---

## 5) Data & Persistence Model

### 5.1 Database Tables

- `channel` — Channel definitions and metadata
- `template` — Reusable schedule templates
- `template_block` — Individual blocks within templates
- `schedule_day` — Daily schedule instances
- `playlog_event` — Computed playlog entries

### 5.2 JSON Columns

- `rule_json` — Series/movie/tag rules and constraints
- `guardrails_json` — Rating and content restrictions
- `ad_policy_json` — Ad pod configuration and rotation rules

### 5.3 Ad Breaks Storage

- Stored per media asset (list of times, origin=ingest|generated|manual)
- Integrated with ingest module's ad break detection
- Manual override capabilities for fine-tuning

### 5.4 Example Rule JSON

```json
{
  "mode": "series",
  "series": ["Cheers"],
  "tags_any": ["sitcoms"],
  "rating_max": null,
  "episode_policy": "syndication"
}
```

```json
{
  "mode": "movie",
  "query": "type:movie AND (tag:family OR (tag:disney AND rating<=PG-13))",
  "tags_any": ["family", "disney"],
  "rating_max": "PG-13"
}
```

---

## 6) Data Access Layer (v0.1)

> Implementation detail: Direct SQLite database access through web application. WebSocket connections provide real-time updates between UI components.

**Database Operations:**

- Template CRUD operations through SQLite ORM/direct queries
- Schedule generation and persistence
- Playlog computation and caching
- Real-time UI updates via Qt signals when data changes

**Key Components:**

- `TemplateManager` — Template CRUD operations
- `ScheduleGenerator` — Generate daily schedules from templates
- `PlaylogComputer` — Compute playlog events from schedules
- `DatabaseSignals` — Qt signals for UI updates

---

## 7) Rule Engine (v0.1)

### 7.1 Content Selection Rules

- **Series rules**: Specific shows, tag-based selection, episode policies
- **Movie rules**: Tag combinations, rating filters, genre restrictions
- **Promo rules**: Ad pod configuration, rotation schedules, category separation

### 7.2 Constraint System

- **Time constraints**: Block placement restrictions, time-of-day rules
- **Rating guardrails**: Content appropriateness for time slots
- **Must-run items**: Required content that must be included
- **Conflict resolution**: Automatic handling of overlapping requirements

### 7.3 Episode Policies

- **Syndication**: Random episode selection from available episodes
- **Serial**: Sequential episode playback (for ongoing series)
- **Circular**: Repeat cycle through available episodes

---

## 8) Performance & Scalability

- **Template caching**: Frequently used templates cached in Qt application memory
- **Lazy loading**: Large content libraries loaded on demand using Qt model/view architecture
- **Batch operations**: Multiple block operations processed efficiently with database transactions
- **Real-time updates**: Qt signals/slots provide immediate UI updates when data changes
- **Background processing**: QThread workers for schedule generation and playlog computation

---

## 9) Error Handling & UX

- **Validation feedback**: Real-time validation of rule configurations
- **Conflict detection**: Visual indicators for scheduling conflicts
- **Recovery options**: Undo/redo for block operations
- **Error context**: Clear error messages with suggested resolutions

---

## 10) Security & Permissions (v0.1)

- **Template ownership**: Users can only modify their own templates
- **Schedule locks**: Prevent concurrent modifications to active schedules
- **Audit trail**: Track all schedule modifications and approvals

---

## 11) Roadmap

### v0.2 Features

- Template overrides (holidays, special events)
- Must-run promos and category separation
- Advanced rule language with complex expressions
- Schedule optimization algorithms

### v0.3 Features

- As-run log integration
- Compliance warnings and reporting
- Ad category separation and rotation
- Multi-channel coordination

### Future Features

- Advanced rule language with scripting
- Graphics overlays and branding
- Emergency alert preemption
- Integration with external traffic systems

---

## 12) Acceptance Criteria (v0.1)

- Drag "Cheers" to any 30-min slot; save/load template persists correctly in SQLite
- Stretch block from 30 → 120 minutes; DB reflects duration
- Open block editor; switch episode_policy to serial; persists
- Create movie rule with tags+rating; persists
- Generate daily schedule from template (e.g., Cheers 24×7)
- Playlog preview shows episodes + ad pods with at least two distinct commercials rotating
- No breaking changes to existing database schema
- Native Windows desktop application with Qt widgets and layouts
- PyInstaller packaging creates single executable (RetroVue.exe)

---

## 13) Integration Points

### 13.1 Ingest Module Integration

- Content metadata from ingest module drives rule-based selection
- Ad break information from ingest module used in playlog generation
- Content availability status affects schedule generation

### 13.2 Future Module Integration

- **Content Browser**: Deep linking to content details from schedule blocks
- **Metadata Editor**: Override content metadata for scheduling purposes
- **Playout Log Viewer**: Real-time schedule execution monitoring
- **Channel Dashboard**: Schedule status and health monitoring

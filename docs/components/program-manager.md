# 📺 Program Manager

The Program Manager is responsible for creating, managing, and scheduling programming content for IPTV channels. It serves as the bridge between the content library and the channel system, enabling automated programming with realistic broadcast timing and transitions.

## 🎯 Business Purpose

The Program Manager transforms the content library into broadcast-ready programming:

- **Programming Creation**: Build program schedules from content library
- **Schedule Management**: Create and manage programming schedules
- **Content Rotation**: Ensure diverse content distribution
- **Timing Control**: Manage realistic broadcast timing and transitions
- **Commercial Integration**: Insert commercials and promotional content

## 🏗️ System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Program Manager                         │
├─────────────────────────────────────────────────────────────┤
│  Schedule Builder  │  Content Rotator  │  Timing Engine   │
├─────────────────────────────────────────────────────────────┤
│                    Programming Services                    │
├─────────────────────────────────────────────────────────────┤
│  ProgramService  │  ScheduleService  │  RotationService   │
├─────────────────────────────────────────────────────────────┤
│                    Domain Entities                         │
├─────────────────────────────────────────────────────────────┤
│  Program  │  Schedule  │  Block  │  Rotation  │  Timing    │
├─────────────────────────────────────────────────────────────┤
│                    Content Integration                     │
├─────────────────────────────────────────────────────────────┤
│  Content Library  │  Commercial Library  │  Metadata      │
└─────────────────────────────────────────────────────────────┘
```

### Data Model Relationships

```
Schedule
├── Program Blocks
│   ├── Content Items (Episodes, Movies)
│   ├── Commercials
│   └── Promotional Content
├── Rotation Rules
│   ├── Frequency Rules
│   ├── Timing Rules
│   └── Content Rules
└── Timing Configuration
    ├── Start Times
    ├── Durations
    └── Transitions
```

## 🔧 Technical Implementation

### 1. Core Services

#### ProgramService

**Purpose**: Manages individual programs and their content

```python
class ProgramService:
    def __init__(self, db: Session):
        self.db = db

    def create_program(self, title: str, content_items: list[ContentItem]) -> Program:
        """Create a new program with specified content."""
        pass

    def add_content_to_program(self, program_id: UUID, content_item: ContentItem):
        """Add content item to existing program."""
        pass

    def calculate_program_duration(self, program: Program) -> int:
        """Calculate total duration of program in milliseconds."""
        pass
```

**Key Methods:**

- `create_program()`: Create new program
- `add_content()`: Add content to program
- `calculate_duration()`: Calculate program length
- `validate_program()`: Validate program content

#### ScheduleService

**Purpose**: Manages programming schedules and timing

```python
class ScheduleService:
    def __init__(self, db: Session):
        self.db = db

    def create_schedule(self, channel_id: UUID, start_time: datetime) -> Schedule:
        """Create a new programming schedule."""
        pass

    def add_program_to_schedule(self, schedule_id: UUID, program: Program, start_time: datetime):
        """Add program to schedule at specific time."""
        pass

    def generate_schedule(self, channel_id: UUID, duration: timedelta) -> Schedule:
        """Automatically generate schedule for specified duration."""
        pass
```

**Key Methods:**

- `create_schedule()`: Create new schedule
- `add_program()`: Add program to schedule
- `generate_schedule()`: Auto-generate schedule
- `validate_schedule()`: Validate schedule timing

#### RotationService

**Purpose**: Manages content rotation and distribution rules

```python
class RotationService:
    def __init__(self, db: Session):
        self.db = db

    def create_rotation_rule(self, content_type: str, frequency: str, constraints: dict) -> RotationRule:
        """Create content rotation rule."""
        pass

    def apply_rotation_rules(self, schedule: Schedule) -> Schedule:
        """Apply rotation rules to schedule."""
        pass

    def check_rotation_compliance(self, schedule: Schedule) -> list[RotationViolation]:
        """Check schedule for rotation rule violations."""
        pass
```

### 2. Domain Entities

#### Program Entity

```python
class Program(Base):
    """Represents a programming block with content."""

    id: UUID = Primary key
    title: str = Program title
    description: Optional[str] = Program description
    duration_ms: int = Total duration in milliseconds
    content_items: list[ContentItem] = List of content in program
    created_at: datetime = When program was created
    updated_at: datetime = Last modification time
```

#### Schedule Entity

```python
class Schedule(Base):
    """Represents a programming schedule for a channel."""

    id: UUID = Primary key
    channel_id: UUID = Foreign key to channel
    start_time: datetime = Schedule start time
    end_time: datetime = Schedule end time
    programs: list[Program] = Programs in schedule
    status: ScheduleStatus = DRAFT | ACTIVE | COMPLETED
    created_at: datetime = When schedule was created
```

#### RotationRule Entity

```python
class RotationRule(Base):
    """Defines content rotation rules and constraints."""

    id: UUID = Primary key
    name: str = Rule name
    content_type: str = Type of content (episode, movie, commercial)
    frequency: str = How often content can repeat
    constraints: dict = Additional constraints
    active: bool = Whether rule is active
```

### 3. Programming Patterns

#### Block Programming

```python
class BlockProgram:
    """Represents a block of programming (e.g., morning news, primetime)."""

    def __init__(self, name: str, start_time: time, duration: timedelta):
        self.name = name
        self.start_time = start_time
        self.duration = duration
        self.content_rules = []

    def add_content_rule(self, rule: ContentRule):
        """Add content selection rule to block."""
        self.content_rules.append(rule)
```

#### Daypart Programming

```python
class DaypartProgram:
    """Represents programming for specific dayparts."""

    DAYPARTS = {
        "morning": (6, 12),      # 6 AM - 12 PM
        "afternoon": (12, 17),   # 12 PM - 5 PM
        "evening": (17, 22),     # 5 PM - 10 PM
        "late_night": (22, 6)    # 10 PM - 6 AM
    }

    def get_daypart_content(self, daypart: str) -> list[ContentItem]:
        """Get content appropriate for daypart."""
        pass
```

## 🎮 User Interfaces

### 1. CLI Interface

#### Program Management Commands

```bash
# Create new program
retrovue program create "Morning News" --duration 2h

# Add content to program
retrovue program add-content <program_id> <episode_id>

# List programs
retrovue program list

# Get program details
retrovue program show <program_id>
```

#### Schedule Management Commands

```bash
# Create schedule
retrovue schedule create <channel_id> --start "2024-01-01 06:00:00"

# Add program to schedule
retrovue schedule add-program <schedule_id> <program_id> --start "06:00:00"

# Generate schedule
retrovue schedule generate <channel_id> --duration 24h

# List schedules
retrovue schedule list
```

#### Rotation Management Commands

```bash
# Create rotation rule
retrovue rotation create-rule "episodes" --frequency "daily" --max-repeats 1

# Apply rotation rules
retrovue rotation apply <schedule_id>

# Check rotation compliance
retrovue rotation check <schedule_id>
```

### 2. Web Interface

#### Program Builder

- **URL**: `/programs`
- **Features**:
  - Visual program builder
  - Content library integration
  - Duration calculations
  - Preview functionality

#### Schedule Manager

- **URL**: `/schedules`
- **Features**:
  - Timeline view of schedules
  - Drag-and-drop program placement
  - Conflict detection
  - Schedule validation

#### Rotation Dashboard

- **URL**: `/rotation`
- **Features**:
  - Rotation rule management
  - Compliance checking
  - Content distribution analysis
  - Rule performance metrics

### 3. API Endpoints

#### Program Endpoints

```python
# Create program
POST /api/programs
# Get program details
GET /api/programs/{program_id}
# Update program
PUT /api/programs/{program_id}
# Add content to program
POST /api/programs/{program_id}/content
```

#### Schedule Endpoints

```python
# Create schedule
POST /api/schedules
# Get schedule details
GET /api/schedules/{schedule_id}
# Add program to schedule
POST /api/schedules/{schedule_id}/programs
# Generate schedule
POST /api/schedules/generate
```

#### Rotation Endpoints

```python
# Create rotation rule
POST /api/rotation/rules
# Apply rotation rules
POST /api/rotation/apply
# Check compliance
GET /api/rotation/compliance/{schedule_id}
```

## 📅 Scheduling System

### Schedule Generation

#### Automatic Schedule Generation

```python
def generate_schedule(channel_id: UUID, duration: timedelta) -> Schedule:
    """Generate programming schedule automatically."""
    schedule = Schedule(channel_id=channel_id, start_time=datetime.now())

    # Get available content
    content_library = get_content_library()

    # Apply daypart rules
    daypart_rules = get_daypart_rules()

    # Apply rotation rules
    rotation_rules = get_rotation_rules()

    # Generate programs
    programs = generate_programs(content_library, daypart_rules, rotation_rules)

    # Add programs to schedule
    current_time = schedule.start_time
    for program in programs:
        schedule.add_program(program, current_time)
        current_time += program.duration

    return schedule
```

#### Daypart Programming Rules

```python
class DaypartRules:
    """Rules for programming different dayparts."""

    RULES = {
        "morning": {
            "content_types": ["news", "talk_show", "educational"],
            "duration_range": (30, 120),  # 30 minutes to 2 hours
            "commercial_frequency": 15,   # Commercials every 15 minutes
        },
        "afternoon": {
            "content_types": ["drama", "comedy", "reality"],
            "duration_range": (30, 60),   # 30 minutes to 1 hour
            "commercial_frequency": 12,   # Commercials every 12 minutes
        },
        "evening": {
            "content_types": ["drama", "comedy", "movie"],
            "duration_range": (60, 180),  # 1 hour to 3 hours
            "commercial_frequency": 10,   # Commercials every 10 minutes
        },
        "late_night": {
            "content_types": ["movie", "documentary", "classic"],
            "duration_range": (90, 240),  # 1.5 hours to 4 hours
            "commercial_frequency": 20,   # Commercials every 20 minutes
        }
    }
```

### Content Rotation

#### Rotation Rules

```python
class RotationRule:
    """Defines how content can be repeated in programming."""

    def __init__(self, content_type: str, frequency: str, constraints: dict):
        self.content_type = content_type
        self.frequency = frequency  # "daily", "weekly", "monthly"
        self.constraints = constraints

    def can_repeat(self, content_item: ContentItem, schedule: Schedule) -> bool:
        """Check if content can be repeated in schedule."""
        last_airing = self.get_last_airing(content_item, schedule)
        if not last_airing:
            return True

        time_since_last = schedule.start_time - last_airing
        return self.check_frequency_constraint(time_since_last)
```

#### Content Distribution

```python
def distribute_content(content_library: list[ContentItem], rules: list[RotationRule]) -> list[ContentItem]:
    """Distribute content according to rotation rules."""
    distributed_content = []

    for rule in rules:
        eligible_content = filter_content_by_rule(content_library, rule)
        distributed_content.extend(eligible_content)

    # Sort by priority and rotation compliance
    return sort_by_rotation_priority(distributed_content)
```

## 🎬 Program Types

### 1. Series Programming

```python
class SeriesProgram:
    """Programming for TV series with episodes."""

    def __init__(self, series: Series, episode_selection: str):
        self.series = series
        self.episode_selection = episode_selection  # "sequential", "random", "weighted"

    def select_episodes(self, count: int) -> list[Episode]:
        """Select episodes according to selection strategy."""
        if self.episode_selection == "sequential":
            return self.get_next_episodes(count)
        elif self.episode_selection == "random":
            return self.get_random_episodes(count)
        elif self.episode_selection == "weighted":
            return self.get_weighted_episodes(count)
```

### 2. Movie Programming

```python
class MovieProgram:
    """Programming for movies and special content."""

    def __init__(self, movie: Movie, commercial_breaks: list[CommercialBreak]):
        self.movie = movie
        self.commercial_breaks = commercial_breaks

    def create_program_with_commercials(self) -> Program:
        """Create program with integrated commercials."""
        program = Program(title=self.movie.title)

        # Add movie content
        program.add_content(self.movie)

        # Insert commercial breaks
        for break_time, commercials in self.commercial_breaks:
            program.insert_commercials_at(break_time, commercials)

        return program
```

### 3. Block Programming

```python
class BlockProgram:
    """Programming for themed content blocks."""

    def __init__(self, theme: str, content_items: list[ContentItem]):
        self.theme = theme
        self.content_items = content_items

    def create_themed_block(self, duration: timedelta) -> Program:
        """Create themed programming block."""
        program = Program(title=f"{self.theme} Block")

        # Select content that fits theme and duration
        selected_content = self.select_content_for_duration(duration)

        for content in selected_content:
            program.add_content(content)

        return program
```

## 🔧 Configuration

### Schedule Configuration

```python
# Schedule generation settings
schedule_config = {
    "default_duration": "24h",
    "daypart_rules": {
        "morning": {"start": "06:00", "end": "12:00"},
        "afternoon": {"start": "12:00", "end": "17:00"},
        "evening": {"start": "17:00", "end": "22:00"},
        "late_night": {"start": "22:00", "end": "06:00"}
    },
    "commercial_insertion": {
        "frequency": 15,  # minutes
        "duration": 2,    # minutes
        "max_per_hour": 4
    }
}
```

### Rotation Configuration

```python
# Content rotation settings
rotation_config = {
    "episode_rotation": {
        "frequency": "weekly",
        "max_repeats_per_week": 1,
        "min_gap_hours": 24
    },
    "movie_rotation": {
        "frequency": "monthly",
        "max_repeats_per_month": 1,
        "min_gap_days": 7
    },
    "commercial_rotation": {
        "frequency": "daily",
        "max_repeats_per_day": 3,
        "min_gap_hours": 4
    }
}
```

## 📊 Monitoring and Analytics

### Key Metrics

- **Schedule compliance**: Adherence to programming rules
- **Content distribution**: How content is distributed across time
- **Rotation effectiveness**: Content freshness and variety
- **Timing accuracy**: Actual vs. planned timing
- **Commercial integration**: Commercial placement effectiveness

### Performance Monitoring

```python
def monitor_programming_performance():
    return {
        "schedule_accuracy": calculate_schedule_accuracy(),
        "content_distribution": analyze_content_distribution(),
        "rotation_compliance": check_rotation_compliance(),
        "commercial_integration": analyze_commercial_placement()
    }
```

## 🚀 Future Enhancements

### Planned Features

- **Machine Learning**: AI-powered content selection and scheduling
- **Advanced Analytics**: Detailed programming performance metrics
- **Dynamic Scheduling**: Real-time schedule adjustments
- **Content Recommendations**: Intelligent content suggestions
- **Audience Targeting**: Programming based on viewer demographics

### Integration Opportunities

- **EPG Integration**: Export programming data to EPG systems
- **Analytics Integration**: Connect with viewing analytics
- **Content Providers**: Integration with content recommendation APIs
- **Social Media**: Automated social media promotion of programming

---

_The Program Manager provides the intelligence and automation needed to create engaging, well-structured programming schedules that maximize content value and viewer experience._

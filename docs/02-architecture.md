# Architecture

## High-Level Architecture

Plugins/Bots
    ↓
Collector Layer
    ↓
Queue Engine
    ↓
Processing Layer
    ↓
Validation Layer
    ↓
Storage Layer
    ↓
API Layer
    ↓
Afra Smart Assistant

## Core Components

### Core Engine
Responsible for:

- Bootstrapping
- Plugin loading
- Config management
- Worker management
- Queue orchestration

### Scheduler Engine
Responsible for:

- Time-based execution
- Speed profile assignment
- Automatic start/stop
- Safe shutdown
- Resume handling

### Queue Engine
Responsible for:

- Job scheduling
- Retry handling
- Dead-letter queue
- Worker assignment
- Priority management

### Plugin Manager
Responsible for:

- Plugin discovery
- Plugin validation
- Plugin lifecycle management

### Processing Layer
Responsible for:

- Cleaning
- Deduplication
- Validation
- Text normalization
- Data enrichment

### Storage Layer
Responsible for:

- Entity storage
- Audit logs
- Speed profiles
- Schedules
- Operational logs

### API Layer
Responsible for:

- External API access
- Bot control
- Queue status
- Lead delivery
- Future integration with Afra Smart Assistant

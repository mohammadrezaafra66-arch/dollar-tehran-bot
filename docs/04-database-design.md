# Database Design

## Database Philosophy

Database is the primary source of truth.

Excel is only:
- Human-friendly import
- Human-friendly export

## Phase Strategy

### Phase 1
SQLite

### Phase 2
PostgreSQL

### Phase 3
Redis + PostgreSQL

## Required Tables

- bots
- plugins
- jobs
- schedules
- speed_profiles
- sources
- sellers
- ads
- phones
- leads
- extraction_runs
- audit_logs
- operational_logs

## Design Rules

- Every table must have UUID primary keys
- Every table must include created_at and updated_at
- Soft delete preferred over hard delete
- Audit logs must be immutable
- Queue states must be persistent

## Queue Persistence

Jobs must survive:

- Restart
- Crash
- Unexpected shutdown
- Network interruption

## Future Scalability

The database layer must be abstracted to allow migration from SQLite to PostgreSQL without changing business logic.

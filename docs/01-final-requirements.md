# Final Requirements

## Divar Lead Extraction Requirements

The Divar extraction bot must support:

- Configurable extraction speed
- Scheduled enable/disable behavior
- Multiple speed profiles during different time windows
- Queue-driven execution
- Retry policies
- Checkpoint recovery
- Operational logging
- Audit trail logging
- Entity-based storage

## Speed Profiles

Supported profiles:

- safe
- slow
- normal
- fast
- test
- custom

Each speed profile must support:

- delay_between_pages
- delay_between_ads
- delay_before_contact_click
- delay_after_contact_click
- max_ads_per_hour
- max_parallel_workers
- retry_policy
- captcha_stop_policy

## Scheduling Requirements

Bots must support:

- Scheduled execution windows
- Automatic stop/start
- Per-time-window speed profiles
- Emergency stop
- Safe shutdown
- Resume from checkpoint

## Entity Requirements

Main entities:

- Seller
- Ad
- Lead
- Phone
- Message
- Job
- ExtractionRun
- SpeedProfile
- Schedule
- AuditLog

## Platform Requirements

- Plugin architecture
- Queue architecture
- API-first architecture
- Database-first architecture
- Excel only for import/export
- Operational observability
- Modular structure

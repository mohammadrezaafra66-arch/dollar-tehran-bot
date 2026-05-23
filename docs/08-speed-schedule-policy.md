# Speed and Schedule Policy

## Goal

Extraction speed and execution schedules must never be hardcoded.

All operational behavior must be configurable through:

- Config files
- Database
- Temporary operations panel
- Future APIs

## Supported Speed Profiles

- safe
- slow
- normal
- fast
- test
- custom

## Speed Profile Fields

- delay_between_pages
- delay_between_ads
- delay_before_contact_click
- delay_after_contact_click
- max_ads_per_hour
- max_messages_per_hour
- max_parallel_workers
- retry_policy
- captcha_stop_policy

## Scheduling Requirements

Bots must support:

- Time-based enable/disable
- Per-time-window speed profiles
- Automatic pause
- Safe shutdown
- Resume from checkpoint

## Example

08:00 - 11:00 => safe
11:00 - 14:00 => slow
17:00 - 21:00 => normal
23:00 - 06:00 => fast

## Queue Integration

Speed policies must affect:

- Worker allocation
- Queue throughput
- Retry delays
- Parallelism
- Job scheduling

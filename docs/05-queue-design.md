# Queue Design

## Queue Goals

The queue system must support:

- Scheduled jobs
- Retry policies
- Priority-based execution
- Dead-letter queue
- Worker locking
- Pause/resume
- Safe shutdown
- Checkpoint recovery

## Job States

- pending
- scheduled
- running
- paused
- retrying
- failed
- completed
- dead_letter

## Required Job Fields

- id
- job_type
- plugin_name
- priority
- payload
- speed_profile
- status
- retry_count
- max_retry
- scheduled_at
- locked_by_worker
- locked_until
- error_message
- created_at
- updated_at

## Dead Letter Queue

Jobs that fail repeatedly must move into a dead-letter queue for manual investigation.

## Speed Profile Awareness

The queue engine must apply:

- Speed limits
- Worker limits
- Time-window policies
- Retry delays

based on active speed profiles.

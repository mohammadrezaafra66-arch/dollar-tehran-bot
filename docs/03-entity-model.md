# Entity Model

## Purpose

The platform must be entity-based, not Excel-row-based.

Every important object in the system must have a stable identity and relationships.

## Core Entities

### Bot
Represents an automation bot instance.

Fields:
- id
- name
- plugin_name
- status
- active_speed_profile
- created_at
- updated_at

### Plugin
Represents a modular extraction plugin.

Fields:
- id
- name
- version
- enabled
- supported_job_types
- config_schema

### Job
Represents a queued unit of work.

Fields:
- id
- plugin_name
- job_type
- status
- priority
- payload
- speed_profile
- scheduled_at
- retry_count
- max_retry
- created_at
- updated_at

### Source
Represents a source website, channel or URL.

Fields:
- id
- source_type
- platform
- url
- reliability_score
- last_success_at
- last_failure_at

### Seller
Represents a discovered seller or business.

Fields:
- id
- source_platform
- display_name
- city
- province
- normalized_name
- confidence_score
- created_at
- updated_at

### Ad
Represents a listing or advertisement.

Fields:
- id
- seller_id
- source_id
- title
- description
- price
- url
- extracted_at

### Phone
Represents a phone number.

Fields:
- id
- owner_entity_type
- owner_entity_id
- phone
- normalized_phone
- phone_type
- confidence_score
- source_method

### Lead
Represents a sales-ready extracted entity.

Fields:
- id
- seller_id
- lead_score
- readiness_status
- confidence_score
- tags
- created_at
- updated_at

### ExtractionRun
Represents a full execution run.

Fields:
- id
- bot_id
- started_at
- finished_at
- status
- total_jobs
- successful_jobs
- failed_jobs

### AuditLog
Represents an immutable operational event.

Fields:
- id
- actor_type
- actor_id
- action
- entity_type
- entity_id
- before_data
- after_data
- created_at

## Rule

Excel exports must be generated from entities. Excel must never become the source of truth.

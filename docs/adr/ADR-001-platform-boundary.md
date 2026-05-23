# ADR-001 - Platform Boundary

## Status
Accepted

## Context

There is a risk that Afra Automation Platform becomes:

- A CRM
- A final business panel
- A final AI business assistant
- A sales management platform

This would create uncontrolled architectural complexity.

## Decision

Afra Automation Platform will ONLY handle:

- Extraction
- Cleaning
- Validation
- Queue management
- Scheduling
- Storage
- Audit logging
- API delivery

Final business logic and CRM workflows must exist in Afra Smart Assistant.

## Consequences

Benefits:

- Clear boundaries
- Lower complexity
- Better scalability
- Cleaner architecture

Tradeoffs:

- Requires strong API integration
- Requires separate web application

# API Contract

## Goal

All future integrations with Afra Smart Assistant must happen through APIs.

## Bot APIs

GET /api/bots
POST /api/bots/{id}/start
POST /api/bots/{id}/stop
GET /api/bots/{id}/status

## Queue APIs

GET /api/jobs
POST /api/jobs
GET /api/jobs/{id}
POST /api/jobs/{id}/retry
POST /api/jobs/{id}/cancel

## Schedule APIs

GET /api/schedules
POST /api/schedules
PUT /api/schedules/{id}

## Speed Profile APIs

GET /api/speed-profiles
POST /api/speed-profiles
PUT /api/speed-profiles/{id}

## Lead APIs

GET /api/leads
GET /api/leads/{id}

## Operational APIs

GET /api/logs
GET /api/audit-logs
GET /api/extraction-runs

## Design Rules

- JSON only
- Versioned APIs
- Authentication-ready
- Async-friendly
- Queue-aware
- Plugin-aware

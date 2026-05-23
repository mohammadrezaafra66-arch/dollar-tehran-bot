# Plugin Architecture

## Goal

Each automation bot must be implemented as an isolated plugin.

The core platform must not depend on bot-specific logic.

## Plugin Structure

plugins/
  divar/
    plugin.yaml
    driver.py
    parser.py
    schemas.py
    config_schema.yaml
    tests/

## Plugin Responsibilities

Each plugin must define:

- Supported job types
- Required configuration
- Output schemas
- Retry behavior
- Supported speed profiles
- Rate limits
- Validation rules

## Plugin Isolation

Plugins must:

- Avoid modifying core architecture
- Use shared queue APIs
- Use shared entity schemas
- Use shared logging system
- Use shared audit system

## Future Plugins

- Divar
- Google Maps
- Torob
- Rubika
- Instagram

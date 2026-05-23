# Afra Automation Platform

Afra Automation Platform is a modular automation ecosystem responsible for:

- Data extraction
- Data cleaning
- Data normalization
- Data validation
- Queue-based processing
- Audit logging
- Operational monitoring
- API-based data delivery

This platform is NOT:

- Final CRM
- Final business dashboard
- Final decision-making engine
- Final AfraKala web application

Its role is to act as the operational and data bridge between automation bots and the Afra Smart Assistant web application.

---

# Core Architecture Principles

- Plugin Architecture
- Queue-driven execution
- API-first design
- Config-driven behavior
- Database as source of truth
- Modular architecture
- Operational observability
- Auditability
- Scalability

---

# Planned Plugins

- Divar Lead Extractor
- Google Maps Extractor
- Torob Extractor
- Rubika Extractor
- Instagram Extractor

---

# Key Features

- Configurable speed profiles
- Scheduled execution windows
- Dynamic bot enable/disable
- Retry policies
- Checkpoint recovery
- Entity-based storage
- Audit trail logging
- Data confidence scoring
- Source reliability analysis
- Operational learning layer

---

# Important Boundary

Afra Automation Platform only handles extraction and operational processing.

Final business logic, CRM workflows, pricing logic and AI business decisions must exist inside the Afra Smart Assistant web application.

---

# Long-Term Goal

All bots, schedules, speed profiles, queues, logs and outputs must eventually be controlled through APIs by the Afra Smart Assistant web application.

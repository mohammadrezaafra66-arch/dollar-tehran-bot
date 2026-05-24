# Architecture Audit and Integration Plan

## Current Finding

The repository entrypoint currently uses:

```python
from afra_market_data.cli import main

if __name__ == '__main__':
    main()
```

This means the repository already has, or is expected to have, a package named `afra_market_data` as the main application package.

At the same time, the new Torob foundation work introduced a parallel `app/` structure containing:

- `app/core/config_loader.py`
- `app/core/logger.py`
- `app/core/queue_manager.py`
- `app/core/checkpoint_engine.py`
- `app/db/storage.py`
- `app/runtime/worker.py`
- `app/runtime/scheduler.py`
- `app/browser/browser_manager.py`
- `app/browser/anti_detection.py`
- `app/drivers/base_driver.py`
- `app/drivers/torob_driver.py`

This is useful foundation code, but keeping it permanently parallel to `afra_market_data` is dangerous.

## Main Risk

The project may develop two competing architectures:

1. Existing package: `afra_market_data`
2. New package: `app`

If left unresolved, this can cause:

- Import conflicts
- Duplicate config systems
- Duplicate queue systems
- Duplicate database layers
- Confusing entrypoints
- Hard-to-debug runtime behavior
- Future merge conflicts

## Recommended Direction

The recommended direction is to make `afra_market_data` the official package and gradually migrate the new foundation modules into it.

Suggested target structure:

```text
afra_market_data/
  cli.py
  core/
    config_loader.py
    logger.py
    queue_manager.py
    checkpoint_engine.py
  db/
    storage.py
  runtime/
    scheduler.py
    worker.py
  browser/
    browser_manager.py
    anti_detection.py
  drivers/
    base_driver.py
    torob_driver.py
  exporters/
  panel/
  services/
```

## Migration Plan

### Step 1: Confirm existing package structure

Find and inspect:

- `afra_market_data/cli.py`
- `afra_market_data/__init__.py`
- Existing config modules
- Existing database modules
- Existing scraper or fetcher modules

### Step 2: Move new foundation modules

Move these modules from `app/` to `afra_market_data/`:

- `app/core/*` -> `afra_market_data/core/*`
- `app/db/*` -> `afra_market_data/db/*`
- `app/runtime/*` -> `afra_market_data/runtime/*`
- `app/browser/*` -> `afra_market_data/browser/*`
- `app/drivers/*` -> `afra_market_data/drivers/*`

### Step 3: Update imports

Replace imports such as:

```python
from app.core.logger import PlatformLogger
```

with:

```python
from afra_market_data.core.logger import PlatformLogger
```

### Step 4: Keep `main.py` unchanged

The current `main.py` should remain the stable public entrypoint.

It should continue to call:

```python
from afra_market_data.cli import main
```

### Step 5: Extend CLI

The CLI should support commands such as:

```bash
python main.py torob run
python main.py torob enqueue
python main.py torob status
python main.py scheduler run
python main.py panel api
```

### Step 6: Remove duplicate `app/` once migration is complete

After migration and tests, `app/` should either be removed or kept only if it is the legacy Google Maps package. It must not remain as a second platform architecture.

## Immediate Next Step

Before writing more crawler code, migrate the new foundation modules under `afra_market_data` and wire the CLI to load config, initialize database, enqueue a sample Torob job, and run one worker in dry-run mode.

## Status

- Requirements document added: done
- Foundation modules added under `app/`: done
- Architecture audit: this document
- Migration to `afra_market_data`: pending
- Real Torob extraction: pending
- Local panel integration: pending

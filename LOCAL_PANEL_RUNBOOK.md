# Local Panel Runbook

## Run

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn local_panel_app:app --reload --host 127.0.0.1 --port 8090
```

## Protected mode

Optional local admin protection can be enabled before running the panel:

```powershell
$env:AFRA_PANEL_ADMIN_PASSWORD="change-this-password"
uvicorn local_panel_app:app --reload --host 127.0.0.1 --port 8090
```

When protected mode is enabled, enter the same password in the Admin field in the panel UI.

## Open

- Panel home: http://127.0.0.1:8090
- API docs: http://127.0.0.1:8090/docs

## Smoke test

1. `GET /api/health`
2. `GET /api/auth-mode`
3. `GET /api/bots`
4. `GET /api/google-maps/runner-exists`
5. `POST /api/google-maps/inputs/sample`
6. `POST /api/google-maps/manage/sample`
7. `POST /api/google-maps/request-run`
8. `GET /api/google-maps/queue`
9. `GET /api/google-maps/worker-state`
10. `POST /api/google-maps/outputs/sample`
11. `POST /api/google-maps/logs/sample`
12. `GET /api/google-maps/downloads`

## Worker

```powershell
python panel_worker.py
```

The worker reads `data/panel_job_requests.jsonl`, prepares the first queued Google Maps job, and writes the worker state to `data/panel_worker_state.json`.

## Launcher

```powershell
python run_panel_job.py
```

The launcher currently verifies that the worker state file exists and is ready for the runtime handoff.

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

1. `GET /api/health` and confirm `runner.exists` is true.
2. `GET /api/auth-mode`
3. `GET /api/bots`
4. `GET /api/google-maps/runner-exists`
5. `POST /api/google-maps/inputs/sample`
6. `POST /api/google-maps/manage/sample`
7. `POST /api/google-maps/request-run`
8. `GET /api/google-maps/queue`
9. `python panel_worker.py`
10. `GET /api/google-maps/worker-state`
11. `GET /api/google-maps/outputs`
12. `GET /api/google-maps/logs`
13. `GET /api/google-maps/downloads`
14. Download an output file from `/api/google-maps/download/{file_name}` if files exist.

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

## Output discovery

The panel scans these folders:

- `google-maps-bot/output`
- `google-maps-bot/logs`

Output files can be downloaded through the panel UI or through:

```text
/api/google-maps/download/{file_name}
```

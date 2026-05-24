# Local Panel Runbook

## Run

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn local_panel_app:app --reload --host 127.0.0.1 --port 8090
```

## Open

- Panel home: http://127.0.0.1:8090
- API docs: http://127.0.0.1:8090/docs

## Smoke test

1. `GET /api/health`
2. `GET /api/bots`
3. `GET /api/google-maps/runner-exists`
4. `POST /api/google-maps/inputs/sample`
5. `POST /api/google-maps/manage/sample`
6. `POST /api/google-maps/request-run`
7. `GET /api/google-maps/queue`
8. `POST /api/google-maps/outputs/sample`
9. `POST /api/google-maps/logs/sample`
10. `GET /api/google-maps/downloads`

## Worker

```powershell
python panel_worker.py
```

The worker reads `data/panel_job_requests.jsonl` and resolves queued Google Maps jobs to `google-maps-bot/run.py`.

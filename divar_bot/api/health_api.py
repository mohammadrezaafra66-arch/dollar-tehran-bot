import os

from flask import Flask, jsonify

from divar_bot.core.health import HealthCheckService
from divar_bot.core.metrics import MetricsRegistry
from divar_bot.core.runtime_settings import RuntimeSettings
from divar_bot.core.runtime_status import RuntimeStatus
from divar_bot.db.sqlite import SQLiteManager


app = Flask(__name__)

settings = RuntimeSettings.from_env()
settings.ensure_directories()

metrics = MetricsRegistry()
database = SQLiteManager(db_path=str(settings.database_path))
runtime_status = RuntimeStatus(instance_id=settings.instance_id)
health_service = HealthCheckService(
    db=database,
    queue=True,
    metrics=metrics,
)


@app.get('/health')
def health():
    payload = health_service.check()
    payload['runtime'] = runtime_status.snapshot()
    payload['instance_id'] = settings.instance_id
    return jsonify(payload)


@app.get('/live')
def live():
    return jsonify({
        'status': 'alive',
        'instance_id': settings.instance_id,
    })


@app.get('/ready')
def ready():
    payload = health_service.check()
    is_ready = payload.get('status') == 'ok'

    return jsonify({
        'ready': is_ready,
        'instance_id': settings.instance_id,
        'checks': payload,
    }), 200 if is_ready else 503


@app.get('/metrics')
def metrics_endpoint():
    snapshot = metrics.snapshot()
    snapshot['instance_id'] = settings.instance_id
    return jsonify(snapshot)


if __name__ == '__main__':
    port = int(os.getenv('DIVAR_BOT_HEALTH_PORT', '8080'))
    app.run(host='0.0.0.0', port=port)

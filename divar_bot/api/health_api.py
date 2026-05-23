from flask import Flask, jsonify

from divar_bot.core.health import HealthCheckService
from divar_bot.core.metrics import MetricsRegistry
from divar_bot.db.sqlite import SQLiteManager


app = Flask(__name__)

metrics = MetricsRegistry()
database = SQLiteManager()
health_service = HealthCheckService(
    db=database,
    queue=True,
    metrics=metrics,
)


@app.get('/health')
def health():
    return jsonify(health_service.check())


@app.get('/metrics')
def metrics_endpoint():
    return jsonify(metrics.snapshot())

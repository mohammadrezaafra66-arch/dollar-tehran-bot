# Afra Divar Bot Production Deployment

This guide describes how to deploy the Divar Bot module as part of the Afra Automation Platform.

## Runtime assumptions

The runtime is designed for Kubernetes and expects these infrastructure dependencies:

- Kafka for durable event transport
- Redis for distributed rate limiting and idempotency
- etcd for leader election and distributed leases
- Prometheus for scraping `/metrics`
- Grafana for dashboards
- Persistent volume for local WAL and snapshots

## Required configuration

Runtime behavior must be controlled through environment variables, ConfigMaps, and Secrets. Do not hard-code paths, credentials, timeouts, or queue settings in Python code.

Important variables:

```bash
AFRA_ENVIRONMENT=production
AFRA_SERVICE_NAME=divar-bot
AFRA_HEALTH_PORT=8080
AFRA_STATE_DIR=/var/lib/afra-runtime
REDIS_URL=redis://redis:6379/0
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
ETCD_HOST=etcd
DIVAR_BOT_INSTANCE_ID=<pod-name>
```

## Kubernetes deployment

Apply manifests in this order:

```bash
kubectl apply -f deploy/k8s/runtime-config.yaml
kubectl apply -f deploy/k8s/statefulset.yaml
kubectl apply -f deploy/k8s/hpa.yaml
kubectl apply -f deploy/k8s/pdb.yaml
kubectl apply -f deploy/k8s/probes.yaml
```

## Health endpoints

The container exposes:

- `/healthz` for liveness
- `/readyz` for readiness
- `/metrics` for Prometheus
- `/snapshot` for incident debugging

A pod in draining mode must return `ready=false` so Kubernetes stops sending it new work before termination.

## Observability

Prometheus alert rules:

```bash
kubectl apply -f deploy/prometheus/alerts.yml
```

Grafana dashboard:

```text
deploy/grafana/dashboard.json
```

## Rollout safety

Before terminating, workers must enter draining mode. The runtime should stop accepting new jobs, finish or safely route in-flight jobs, release browser leases, and only then exit.

## Failure recovery

WAL state is stored under:

```bash
/var/lib/afra-runtime
```

This path should be backed by a persistent volume. On restart, the runtime can replay valid WAL records and ignore corrupted lines unless strict recovery is enabled.

## Scaling guidance

Start small:

```text
replicas: 3
maxReplicas: 50
```

Do not scale to 50 instances until:

- Redis rate limiter is active
- Kafka consumer groups are healthy
- browser pool metrics are visible
- Prometheus alerts are loaded
- chaos tests pass in CI

## Security notes

Do not commit real secrets. `deploy/k8s/runtime-config.yaml` contains placeholder values only. Production values must be injected through Kubernetes Secrets or an external secrets manager.

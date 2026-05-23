import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimeSettings:
    instance_id: str
    base_dir: Path
    data_dir: Path
    logs_dir: Path
    screenshots_dir: Path
    database_path: Path
    default_timeout_ms: int
    browser_timeout_ms: int
    worker_poll_interval_seconds: int
    shutdown_grace_seconds: int
    max_workers: int

    @classmethod
    def from_env(cls):
        base_dir = Path(os.getenv('DIVAR_BOT_BASE_DIR', '.')).resolve()
        instance_id = os.getenv('DIVAR_BOT_INSTANCE_ID', 'local-dev')
        data_dir = Path(os.getenv('DIVAR_BOT_DATA_DIR', base_dir / 'data')).resolve()
        logs_dir = Path(os.getenv('DIVAR_BOT_LOGS_DIR', base_dir / 'logs')).resolve()
        screenshots_dir = Path(os.getenv('DIVAR_BOT_SCREENSHOTS_DIR', base_dir / 'screenshots')).resolve()
        database_path = Path(os.getenv('DIVAR_BOT_DATABASE_PATH', data_dir / f'{instance_id}.db')).resolve()

        return cls(
            instance_id=instance_id,
            base_dir=base_dir,
            data_dir=data_dir,
            logs_dir=logs_dir,
            screenshots_dir=screenshots_dir,
            database_path=database_path,
            default_timeout_ms=int(os.getenv('DIVAR_BOT_DEFAULT_TIMEOUT_MS', '30000')),
            browser_timeout_ms=int(os.getenv('DIVAR_BOT_BROWSER_TIMEOUT_MS', '45000')),
            worker_poll_interval_seconds=int(os.getenv('DIVAR_BOT_WORKER_POLL_INTERVAL_SECONDS', '5')),
            shutdown_grace_seconds=int(os.getenv('DIVAR_BOT_SHUTDOWN_GRACE_SECONDS', '30')),
            max_workers=int(os.getenv('DIVAR_BOT_MAX_WORKERS', '2')),
        )

    def ensure_directories(self):
        for path in [self.data_dir, self.logs_dir, self.screenshots_dir]:
            path.mkdir(parents=True, exist_ok=True)

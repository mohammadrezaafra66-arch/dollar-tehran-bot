from app.core.queue import QueueManager
from app.core.worker import Worker


def bootstrap():
    queue = QueueManager()

    queue.add_job(
        job_type='divar_extract',
        plugin_name='divar',
        payload={
            'url': 'https://divar.ir'
        },
        priority=10,
        speed_profile='test'
    )

    worker = Worker()
    worker.process_next_job()


if __name__ == '__main__':
    bootstrap()

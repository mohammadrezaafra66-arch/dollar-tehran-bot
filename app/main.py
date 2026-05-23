from app.core.queue import QueueManager


def bootstrap():
    queue = QueueManager()

    queue.add_job(
        job_type='bootstrap_test',
        plugin_name='divar',
        payload={'status': 'test'}
    )


if __name__ == '__main__':
    bootstrap()

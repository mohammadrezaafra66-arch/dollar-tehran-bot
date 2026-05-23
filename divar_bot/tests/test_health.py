from divar_bot.core.health import HealthCheckService


class FakeDB:
    class _Conn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

        def execute(self, query):
            return 1

    def connection(self):
        return self._Conn()


def test_health_ok():
    service = HealthCheckService(db=FakeDB(), queue=True, metrics=True)
    result = service.check()

    assert result['status'] == 'ok'
    assert result['database'] == 'ok'


def test_health_without_dependencies():
    service = HealthCheckService()
    result = service.check()

    assert result['database'] == 'not_configured'

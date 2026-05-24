import asyncio


class FailureRecoveryRuntime:
    def __init__(
        self,
        retry_limit: int = 3,
    ):
        self.retry_limit = retry_limit

    async def execute(self, operation):
        attempt = 0

        while attempt < self.retry_limit:
            attempt += 1

            try:
                return await operation()

            except Exception:
                if attempt >= self.retry_limit:
                    raise

                await asyncio.sleep(attempt)

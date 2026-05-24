import asyncio


class RuntimeFlowRetryPolicy:
    def __init__(
        self,
        max_retry_attempts: int,
        retry_backoff_seconds: int,
    ):
        self.max_retry_attempts = max_retry_attempts
        self.retry_backoff_seconds = retry_backoff_seconds

    async def execute(self, operation):
        attempt = 0

        while attempt < self.max_retry_attempts:
            attempt += 1

            try:
                return await operation()

            except Exception:
                if attempt >= self.max_retry_attempts:
                    raise

                await asyncio.sleep(
                    self.retry_backoff_seconds * attempt
                )

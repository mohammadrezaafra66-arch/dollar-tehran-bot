import asyncio


class RubikaRetryPolicy:
    def __init__(
        self,
        max_retry_attempts: int,
    ):
        self.max_retry_attempts = (
            max_retry_attempts
        )

    async def execute(self, operation):
        attempt = 0

        while attempt < self.max_retry_attempts:
            attempt += 1

            try:
                return await operation()

            except Exception:
                if attempt >= self.max_retry_attempts:
                    raise

                await asyncio.sleep(attempt)

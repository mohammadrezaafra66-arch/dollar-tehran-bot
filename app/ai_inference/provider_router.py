from app.ai_inference.circuit_breaker import (
    AIInferenceCircuitBreaker,
)


class AIInferenceProviderRouter:
    def __init__(
        self,
        providers: dict,
        circuit_breaker: AIInferenceCircuitBreaker,
    ):
        self.providers = providers
        self.circuit_breaker = circuit_breaker

    async def infer(
        self,
        provider_name: str,
        payload: dict,
    ):
        if self.circuit_breaker.is_open():
            raise RuntimeError(
                "AI inference circuit breaker is open"
            )

        provider = self.providers.get(provider_name)

        if not provider:
            raise ValueError(
                f"Provider not found: {provider_name}"
            )

        try:
            response = await provider.infer(payload)
            self.circuit_breaker.record_success()
            return response

        except Exception:
            self.circuit_breaker.record_failure()
            raise

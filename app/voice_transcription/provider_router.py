class VoiceTranscriptionProviderRouter:
    def __init__(self, providers: dict):
        self.providers = providers

    async def transcribe(
        self,
        provider_name: str,
        payload: dict,
    ):
        provider = self.providers.get(provider_name)

        if not provider:
            raise ValueError(
                f"Provider not found: {provider_name}"
            )

        return await provider.transcribe(payload)

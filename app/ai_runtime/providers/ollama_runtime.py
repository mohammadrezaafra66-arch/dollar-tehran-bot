import asyncio
import json
from urllib import request

from app.ai_runtime.contracts import (
    AIRequest,
    AIResponse,
    AIServicePort,
)


class OllamaRuntime(AIServicePort):
    def __init__(
        self,
        config,
    ):
        self.config = config

    async def execute(
        self,
        request_payload: AIRequest,
    ) -> AIResponse:
        loop = asyncio.get_running_loop()

        response = await loop.run_in_executor(
            None,
            self._execute_sync,
            request_payload,
        )

        return response

    def _execute_sync(
        self,
        request_payload: AIRequest,
    ):
        body = json.dumps(
            {
                "model": self.config.model_name,
                "prompt": request_payload.payload.get(
                    "prompt",
                    "",
                ),
                "stream": False,
            }
        ).encode()

        req = request.Request(
            url=(
                f"{self.config.api_base_url}/api/generate"
            ),
            data=body,
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with request.urlopen(
            req,
            timeout=self.config.request_timeout_seconds,
        ) as response:
            payload = json.loads(
                response.read().decode()
            )

        return AIResponse(
            payload=payload,
            provider="ollama",
            model=self.config.model_name,
            trace_id=request_payload.trace_id,
        )

    async def health(self):
        return {
            "provider": "ollama",
            "status": "healthy",
        }

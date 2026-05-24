from app.ai_runtime.contracts import AIRequest


class IntelligentDataNormalization:
    def __init__(self, ai_runtime):
        self.ai_runtime = ai_runtime

    async def normalize(self, payload: dict):
        request = AIRequest(
            payload={
                "prompt": (
                    "Normalize this structured data and return clean JSON: "
                    f"{payload}"
                )
            }
        )

        response = await self.ai_runtime.execute(
            request
        )

        return response.payload

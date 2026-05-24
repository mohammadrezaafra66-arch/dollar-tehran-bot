import asyncio
import json
from urllib import request


class RubikaAdapterRuntime:
    def __init__(self, config):
        self.config = config

    async def send_message(
        self,
        sender_id: str,
        chat_id: str,
        text: str,
    ):
        loop = asyncio.get_running_loop()

        return await loop.run_in_executor(
            None,
            self._send_message_sync,
            sender_id,
            chat_id,
            text,
        )

    def _send_message_sync(
        self,
        sender_id: str,
        chat_id: str,
        text: str,
    ):
        payload = json.dumps(
            {
                "sender_id": sender_id,
                "chat_id": chat_id,
                "text": text,
            }
        ).encode()

        req = request.Request(
            url=(
                f"{self.config.api_base_url}/send"
            ),
            data=payload,
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with request.urlopen(
            req,
            timeout=self.config.request_timeout_seconds,
        ) as response:
            return json.loads(
                response.read().decode()
            )

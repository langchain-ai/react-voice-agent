import json
import os
import websockets

from contextlib import asynccontextmanager
from typing import AsyncGenerator, AsyncIterator, Any, Callable, Coroutine

DEFAULT_MODEL = "gpt-4o-realtime-preview-2024-10-01"
DEFAULT_URL = "wss://api.openai.com/v1/realtime"


@asynccontextmanager
async def connect(
    *, api_key: str | None = None, model: str = "", url: str | None = None
) -> AsyncGenerator[
    tuple[
        Callable[[dict[str, Any]], Coroutine[Any, Any, None]],
        AsyncIterator[dict[str, Any]],
    ],
    None,
]:
    """
    async with connect(model="gpt-4o-realtime-preview-2024-10-01") as websocket:
        await websocket.send("Hello, world!")
        async for message in websocket:
            print(message)
    """
    if not model:
        raise ValueError(f"model is required. try '{DEFAULT_MODEL}'")

    headers = {
        "Authorization": f"Bearer {api_key or os.getenv('OPENAI_API_KEY')}",
        "OpenAI-Beta": "realtime=v1",
    }

    url = url or DEFAULT_URL
    url += f"?model={model}"

    websocket = await websockets.connect(url, extra_headers=headers)

    try:

        async def send_event(event: dict[str, Any]) -> None:
            formatted_event = json.dumps(event)
            await websocket.send(formatted_event)

        async def event_stream() -> AsyncIterator[dict[str, Any]]:
            async for raw_event in websocket:
                yield json.loads(raw_event)

        stream: AsyncIterator[dict[str, Any]] = event_stream()

        yield send_event, stream
    finally:
        await websocket.close()

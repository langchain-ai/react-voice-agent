import asyncio
from typing import AsyncIterator, TypeVar
from starlette.websockets import WebSocket

T = TypeVar("T")


async def amerge(*streams: AsyncIterator[T]) -> AsyncIterator[T]:
    """Merge multiple streams into one stream."""
    nexts = {asyncio.create_task(anext(stream)): stream for stream in streams}
    while nexts:
        done, _ = await asyncio.wait(nexts, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            stream = nexts.pop(task)
            try:
                yield task.result()
                nexts[asyncio.create_task(anext(stream))] = stream
            except StopAsyncIteration:
                pass
            except Exception as e:
                for task in nexts:
                    task.cancel()
                raise e


async def websocket_stream(websocket: WebSocket) -> AsyncIterator[str]:
    while True:
        data = await websocket.receive_text()
        yield data

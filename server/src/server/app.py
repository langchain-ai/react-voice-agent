from starlette.websockets import WebSocket

# from server.graph import graph
from server.utils import amerge, websocket_stream
import server.openai as oai

from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.websockets import WebSocket
from starlette.routing import WebSocketRoute, Route
from starlette.staticfiles import StaticFiles
import uvicorn
import asyncio

from typing import AsyncIterator


# async def app(scope, receive, send):
#     websocket = WebSocket(scope=scope, receive=receive, send=send)
#     await websocket.accept()
#     config = ...

#     client = openai.AsyncClient()
#     input, output = client.audio.thingy.start_bidirectional_stream()
#     task: asyncio.Task | None = None
#     lock = asyncio.Lock()

#     async def handle_tool_call(call: ToolIsCalling, config: RunnableConfig, prev: asyncio.Task | None) -> None:
#         if prev is not None:
#             try:
#                 await task
#             except asyncio.CancelledError:
#                 pass
#         result = await graph.ainvoke(call, config)
#         async with lock:
#             await input(result)

#     async for key, chunk in amerge({"mic": websocket.iter_bytes(), "model": output}):
#         if key == "mic":
#             async with lock:
#                 await input(chunk)
#         elif key == "model":
# 	          if chunk is tool_call:
# 	              if task is not None and task.done():
# 	                  task = None
# 	              if task is not None:
# 	                  task.cancel()
# 		            task = asyncio.create_task(handle_tool_call(tool_call, config, task))
# 		        else:
# 				        # it's an audio chunk
# 	              await websocket.send_bytes(chunk)

#     await websocket.close()


async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    browser_receive_stream = websocket_stream(websocket)

    async for data in browser_receive_stream:
        print(data)
        await websocket.send_bytes(data)

    return

    async with oai.connect() as (model_send, model_receive_stream):

        task: asyncio.Task | None = None
        lock = asyncio.Lock()

        async def run_graph(data: dict) -> None:
            async for result in graph.astream(data, mode="custom"):
                await model_send(result)

        async def start_interrupt_graph(data: dict) -> None:
            if task is not None and task.done():
                task = None
            if task is not None:
                task.cancel()
            task = asyncio.create_task(graph.interrupt(data))

        try:
            async for data in amerge(browser_receive_stream, model_receive_stream):
                if isinstance(data, dict):
                    # from model_receive_stream
                    print("model data", data)
                    if data["type"] == "input_audio_buffer.append":
                        websocket.send_bytes(data["audio_buffer"])

                else:
                    # from browser_receive_stream
                    print("browser data", data)
                    audio_chunk = {}
                    await model_send(data)
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            await websocket.close()


async def homepage(request):
    with open("src/server/to_socket.html") as f:
        html = f.read()
        return HTMLResponse(html)


# catchall route to load files from src/server/static


routes = [Route("/", homepage), WebSocketRoute("/ws", websocket_endpoint)]

app = Starlette(debug=True, routes=routes)

app.mount("/", StaticFiles(directory="src/server/static"), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)

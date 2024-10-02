from starlette.websockets import WebSocket

# from server.graph import graph
from server.utils import amerge, websocket_stream
import server.openai as oai

from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.websockets import WebSocket
from starlette.routing import WebSocketRoute, Route
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

    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Microphone to Speaker</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f0f0f0;
        }
        #toggleAudio {
            font-size: 18px;
            padding: 10px 20px;
            cursor: pointer;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            transition: background-color 0.3s;
        }
        #toggleAudio:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <button id="toggleAudio">Start Audio</button>

    <script>
        // Create audio context
        

        // Function to get microphone input and send it to WebSocket
        async function startAudio() {
            try {
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const ws = new WebSocket("ws://localhost:3000/ws");

                ws.onopen = () => {
                    console.log('open')
                    const mediaRecorder = new MediaRecorder(stream);
                    mediaRecorder.ondataavailable = event => {
                        console.log('sending', event.data);
                        if (event.data.size > 0 && ws.readyState === WebSocket.OPEN) {
                        console.log('sent')
                            ws.send(event.data);
                        }
                    };
                    mediaRecorder.start(10);
                };

                ws.onmessage = event => {
                    console.log('message')
                    const audioBuffer = audioContext.decodeAudioData(event.data);
                    const playbackSource = audioContext.createBufferSource();
                    playbackSource.buffer = audioBuffer;
                    playbackSource.connect(audioContext.destination);
                    playbackSource.start();
                };

            } catch (error) {
                console.error('Error accessing the microphone', error);
                alert('Error accessing the microphone. Please check your settings and try again.');
            }
        }

        // Button to toggle audio
        const toggleButton = document.getElementById('toggleAudio');
        let isAudioOn = false;

        toggleButton.addEventListener('click', async () => {
            if (!isAudioOn) {
                await startAudio();
                toggleButton.textContent = 'Stop Audio';
                isAudioOn = true;
            } else {
                audioContext.suspend();
                toggleButton.textContent = 'Start Audio';
                isAudioOn = false;
            }
        });

    </script>
</body>
</html>"""
    return HTMLResponse(html)


routes = [Route("/", homepage), WebSocketRoute("/ws", websocket_endpoint)]

app = Starlette(debug=True, routes=routes)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)

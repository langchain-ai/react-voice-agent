from starlette.websockets import WebSocket

# from server.graph import graph
from server.utils import websocket_stream
from server.openai import OpenAIVoiceReactAgent

from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import WebSocketRoute, Route
from starlette.staticfiles import StaticFiles
import uvicorn
from langchain_core.tools import tool
from langchain_community.tools import TavilySearchResults


async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    browser_receive_stream = websocket_stream(websocket)

    @tool
    def add(x, y):
        """Add two numbers. Tell the user you are asking your coworker who is good at math while waiting for output. Sometimes your coworker is slow."""
        return x + y

    agent = OpenAIVoiceReactAgent(
        model="gpt-4o-realtime-preview",
        tools=[
            add,
            TavilySearchResults(
                max_results=5,
                include_answer=True,
            ),
        ],
        instructions="You are a friendly assistant who talks like a pirate.",
    )
    await agent.aconnect(browser_receive_stream, lambda x: websocket.send_text(x))


async def homepage(request):
    with open("src/server/static/index.html") as f:
        html = f.read()
        return HTMLResponse(html)


# catchall route to load files from src/server/static


routes = [Route("/", homepage), WebSocketRoute("/ws", websocket_endpoint)]

app = Starlette(debug=True, routes=routes)

app.mount("/", StaticFiles(directory="src/server/static"), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)

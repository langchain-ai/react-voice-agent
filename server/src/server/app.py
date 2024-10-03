import uvicorn
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route, WebSocketRoute
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket

from langchain_core.tools import tool
from langchain_openai_voice import OpenAIVoiceReactAgent

from langchain_community.tools import TavilySearchResults

from server.utils import websocket_stream


async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    browser_receive_stream = websocket_stream(websocket)

    @tool
    def add(a: int, b: int):
        """Add two numbers. Please let the user know that you're adding the numbers BEFORE you call the tool"""
        return a + b

    tavily_tool = TavilySearchResults(
        max_results=5,
        include_answer=True,
    )
    tavily_tool.description += "\n\nLet the user know you're asking your friend Tavily for help before you call the tool."

    agent = OpenAIVoiceReactAgent(
        model="gpt-4o-realtime-preview",
        tools=[add],  # no tools for now
        instructions="You are a helpful assistant.",
    )

    await agent.aconnect(browser_receive_stream, websocket.send_text)


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

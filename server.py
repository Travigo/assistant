import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Iterator, List

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from websockets.sync.client import connect as ws_connect

from autogen.io.websockets import IOWebsockets

from vertex import Assistant

PORT = 8084

logger = logging.getLogger(__name__)


def on_connect(iostream: IOWebsockets) -> None:
    logger.info(f"on_connect(): Connected to client using IOWebsockets {iostream}")

    logger.info("on_connect(): Receiving message from client.")

    # get the initial message from the client
    initial_msg = iostream.input()

    print(initial_msg)

    assistant = Assistant()
    assistant.create_chat()
  
    response = assistant.message(initial_msg)
    for part in response.candidates[0].content.parts:
      iostream.print(part.text)

    logger.info("on_connect(): Finished the task successfully.")


html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Autogen websocket test</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off" value="Is there a rail station in Baldock and what is its name and identifier?"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8080/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


@asynccontextmanager
async def run_websocket_server(app: FastAPI) -> AsyncIterator[None]:
    with IOWebsockets.run_server_in_thread(on_connect=on_connect, port=8080) as uri:
        logger.info(f"Websocket server started at {uri}.")

        yield


app = FastAPI(lifespan=run_websocket_server)


@app.get("/")
async def get() -> HTMLResponse:
    return HTMLResponse(html)


async def start_uvicorn() -> None:
    config = uvicorn.Config(app)
    server = uvicorn.Server(config)
    try:
        await server.serve()  # noqa: F704
    except KeyboardInterrupt:
        logger.info("Shutting down server")


if __name__ == "__main__":
    # set the log level to INFO
    logger.setLevel("INFO")
    asyncio.run(start_uvicorn())

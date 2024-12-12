import asyncio
import time

import requests
import httpx


from fastapi import FastAPI, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocket, WebSocketDisconnect

from config.websocket import WebSocketConnectionManager, ws_connection_manager
from feed import router as feed_router
from user.api import router as user_router

app = FastAPI()
app.mount("/static", StaticFiles(directory="feed/posts"))
app.include_router(user_router.router)
app.include_router(feed_router.router)



@app.exception_handler(RequestValidationError)
def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(
        content={"error": exc.errors()[0]["msg"]},
        status_code=status.HTTP_400_BAD_REQUEST,
    )

@app.exception_handler(ValueError)
def value_error_handler(request, exc):
    return JSONResponse(
        content={"error": str(exc)},
        status_code=status.HTTP_400_BAD_REQUEST,
    )

@app.exception_handler(httpx.HTTPStatusError)
def httpx_status_error_handler(request, exc):
    return JSONResponse(
        content={"error": str(exc)},
        status_code=status.HTTP_400_BAD_REQUEST,
    )


@app.get("/")
def health_check_handler():
    return {"ping": "pong"}

#################################


@app.get("/sync")
def sync_handler():
    # 1개 호출 -> 0.5x초
    # 3개 호출 -> 1.62초
    # n개 호출 -> (0.5 * n)초
    start_time = time.perf_counter()
    urls = [
        "https://jsonplaceholder.typicode.com/posts",
        "https://jsonplaceholder.typicode.com/posts",
        "https://jsonplaceholder.typicode.com/posts",
    ]
    responses = []
    for url in urls:
        responses.append(requests.get(url))

    end_time = time.perf_counter()
    return {
        "duration": end_time - start_time,
    }



@app.get("/async")
async def async_handler():
    # 1개 -> 0.58초
    # 3개 -> 0.58초
    start_time = time.perf_counter()

    urls = [
        "https://jsonplaceholder.typicode.com/posts",
        "https://jsonplaceholder.typicode.com/posts",
        "https://jsonplaceholder.typicode.com/posts",
    ]

    async with httpx.AsyncClient() as client:
        tasks = []
        for url in urls:
            tasks.append(client.get(url))
        await asyncio.gather(*tasks)

    end_time = time.perf_counter()
    return {
        "duration": end_time - start_time,
    }

@app.websocket(
    "/ws/rooms/{room_id}/{user_id}"
)
async def websocket_handler(
    room_id: int,
    user_id: int,
    websocket: WebSocket,  # 사용자의 웹소켓 연결(connection)
    connection_manager: WebSocketConnectionManager = Depends(ws_connection_manager),
):
    await connection_manager.connect(
        websocket=websocket, room_id=room_id, user_id=user_id
    )

    try:
        while True:
            content = await websocket.receive_text()
            await connection_manager.broadcast(websocket=websocket, content=content)

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket=websocket)  # 클라이언트 연결 목록에서 제거

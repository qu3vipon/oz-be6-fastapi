import asyncio
import time

import requests
import httpx


from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from item import router as item_router
from user import router as user_router
from user import router_async as user_async_router

app = FastAPI()
app.include_router(item_router.router)
app.include_router(user_router.router, prefix="/sync")
app.include_router(user_async_router.router, prefix="/async")


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

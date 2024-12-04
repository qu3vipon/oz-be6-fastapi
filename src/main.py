from fastapi import FastAPI

from item import router as item_router
from user import router as user_router

app = FastAPI()
app.include_router(item_router.router)
app.include_router(user_router.router)

@app.get("/")
def health_check_handler():
    return {"ping": "pong"}

from fastapi import APIRouter, Path
from pydantic import BaseModel, Field

router = APIRouter(prefix="/users", tags=["User"])

db = [
    {
        "username": "alice",
        "password": "alicezzang123",
    },
    {
        "username": "bob",
        "password": "bobzzang123",
    },
]

class SignUpRequestBody(BaseModel):
    username: str = Field(..., max_length=10)
    password: str

@router.post("")
def sign_up_handler(body: SignUpRequestBody):
    db.append(
        {
            "username": body.username,
            "password": body.password,
        }
    )
    return db

@router.get("/{username}")
def get_user_handler(
    username: str = Path(..., max_length=10),
):
    for user in db:
        if user["username"] == username:
            return user
    return None

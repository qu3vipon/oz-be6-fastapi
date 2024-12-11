import time

import bcrypt
import jwt
from typing import TypedDict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


# password
def hash_password(plain_text: str) -> str:
    hashed_password_bytes: bytes = bcrypt.hashpw(
        plain_text.encode("utf-8"), bcrypt.gensalt()
    )
    return hashed_password_bytes.decode("utf-8")


def check_password(plain_text: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_text.encode("utf-8"), hashed_password.encode("utf-8")
    )


# JWT
SECRET_KEY = "f3d7522be0fbcf3b7fe72edf628fd6cf9eddd93e4f9d2bee32cfd5ea8bb83486"
ALGORITHM = "HS256"


class JWTPayload(TypedDict):
    user_id: int
    isa: int

def encode_access_token(user_id: int) -> str:
    payload: JWTPayload = {
        "user_id": user_id,
        "isa": int(time.time()),
    }
    access_token: str = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return access_token

def decode_access_token(access_token: str) -> JWTPayload:
    return jwt.decode(
        access_token, SECRET_KEY, algorithms=[ALGORITHM]
    )

def authenticate(
    auth_header: HTTPAuthorizationCredentials = Depends(HTTPBearer())
) -> int:
    # 인증 성공
    payload: JWTPayload = decode_access_token(access_token=auth_header.credentials)

    # token 만료 검사
    expiry_seconds = 60 * 60 * 24 * 7
    if payload["isa"] + expiry_seconds < time.time():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    return payload["user_id"]

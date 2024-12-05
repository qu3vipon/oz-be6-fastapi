from pydantic import BaseModel


# 내 정보 조회
class UserMeResponse(BaseModel):
    id: int
    username: str
    password: str


# 다른 사람의 정보 조회
class UserResponse(BaseModel):
    username: str


class JWTResponse(BaseModel):
    access_token: str

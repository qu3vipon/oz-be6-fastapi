from pydantic import BaseModel


# 내 정보를 반환할 때
class UserMeResponse(BaseModel):
    username: str
    password: str


# 다른 사람의 정보를 반환할 때
class UserResponse(BaseModel):
    username: str

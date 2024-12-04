from fastapi import APIRouter, Path, Body, status, HTTPException, Depends
from fastapi.security import HTTPBasicCredentials, HTTPBasic

from user.request import SignUpRequestBody
from user.response import UserMeResponse, UserResponse

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


@router.post(
    "",
    response_model=UserMeResponse,
    status_code=status.HTTP_201_CREATED,
)
def sign_up_handler(body: SignUpRequestBody):
    new_user = {
        "username": body.username,
        "password": body.password,
    }
    db.append(new_user)
    return UserMeResponse(
        username=new_user["username"],
        password=new_user["password"],
    )

# 내 정보 조회
@router.get("/me")
def get_me_handler(
    credentials: HTTPBasicCredentials = Depends(HTTPBasic())
):
    for user in db:
        if user["username"] == credentials.username:
            if user["password"] == credentials.password:
                return UserMeResponse(
                    username=user["username"], password=user["password"]
                )
            else:
                # 비밀번호 틀린 경우
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect password",
                )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )


@router.patch(
    "/me",
    response_model=UserMeResponse,
    status_code=status.HTTP_200_OK,
)
def update_user_handler(
    credentials: HTTPBasicCredentials = Depends(HTTPBasic()),
    new_password: str = Body(..., embed=True),
):
    for user in db:
        if user["username"] == credentials.username:
            if user["password"] != credentials.password:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect password",
                )

            user["password"] = new_password
            return UserMeResponse(
                username=user["username"],
                password=user["password"],
            )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )

# 다른 사람 정보를 조회하는 경우
@router.get(
    "/{username}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
def get_user_handler(
    username: str = Path(..., max_length=10),
):
    for user in db:
        if user["username"] == username:
            return UserResponse(username=user["username"])

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )




@router.delete(
    "/{username}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
def delete_user_handler(
    username: str = Path(..., max_length=10)
):
    for user in db:
        if user["username"] == username:
            db.remove(user)
            return

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )

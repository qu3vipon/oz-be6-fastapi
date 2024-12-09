import asyncio
from fastapi import APIRouter, Path, Body, status, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from pydantic import constr
from sqlalchemy.orm import Session

from config.cache import redis_client
from config.database.connection import get_session
from user.authentication import check_password, encode_access_token, authenticate
from user.email_service import send_otp
from user.models import User
from user.otp_service import create_otp
from user.repository import UserRepository
from user.request import SignUpRequestBody
from user.response import UserMeResponse, UserResponse, JWTResponse

router = APIRouter(prefix="/users", tags=["SyncUser"])

async def send_welcome_email(username):
    await asyncio.sleep(5)
    print(f"{username}님 회원가입을 환영합니다!")


@router.post(
    "",
    response_model=UserMeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def sign_up_handler(
    body: SignUpRequestBody,
    background_tasks: BackgroundTasks,
    user_repo: UserRepository = Depends(),
):
    new_user = User.create(username=body.username, password=body.password)
    user_repo.save(user=new_user)
    background_tasks.add_task(send_welcome_email, username=new_user.username)
    return UserMeResponse.model_validate(obj=new_user)

@router.post(
    "/login",
    response_model=JWTResponse,
    status_code=status.HTTP_200_OK,
)
def login_handler(
    credentials: HTTPBasicCredentials = Depends(HTTPBasic()),
    user_repo: UserRepository = Depends(),
):
    if user := user_repo.get_user_by_username(username=credentials.username):
        if check_password(
            plain_text=credentials.password, hashed_password=user.password
        ):
            return JWTResponse(
                access_token=encode_access_token(username=user.username),
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )

# OTP 발급 API
# : POST /users/email/otp
@router.post(
    "/email/otp",
    status_code=status.HTTP_200_OK,
)
def create_email_otp_handler(
    background_tasks: BackgroundTasks,
    username: str = Depends(authenticate),
    email: str = Body(
        ...,
        pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
        embed=True,
        examples=["admin@example.com"],
    ),
    user_repo: UserRepository = Depends(),
):
    # 1) 이미 회원가입한 사용자가 이메일 인증을 위해 이메일 주소 입력
    if not (user := user_repo.get_user_by_username(username=username)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # 2) 3분 TTL 걸고 OTP를 Redis 저장
    otp: int = create_otp()
    cache_key: str = f"users:{user.id}:email:otp"
    redis_client.hset(name=cache_key, mapping={"otp": otp, "email": email})
    redis_client.expire(cache_key, 3 * 60)

    # 3) 해당 이메일 주소로 OTP 코드(6자리 숫자) 전송
    background_tasks.add_task(send_otp, email=email, otp=otp)
    return {"detail": "Success"}


# OTP 인증 API
# : POST /users/email/otp/verify
@router.post("/email/otp/verify")
def verify_email_otp_handler(
    username: str = Depends(authenticate),
    otp: int = Body(..., embed=True, ge=100_000, le=999_999),
    user_repo: UserRepository = Depends(),
):
    # 1) 사용자가 이메일로 받은 OTP를 서버에 전달
    if not (user := user_repo.get_user_by_username(username=username)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # 2) OTP를 검증(Redis에서 조회)
    cached_data = redis_client.hgetall(f"users:{user.id}:email:otp")
    if not (cached_otp := cached_data.get("otp")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP not found",
        )

    if otp != int(cached_otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP mismatch",
        )

    email: str = cached_data.get("email")
    user.update_email(email=email)
    user_repo.save(user=user)
    return UserMeResponse.model_validate(obj=user)


# 내 정보 조회
@router.get("/me")
def get_me_handler(
    username: str = Depends(authenticate),
    user_repo: UserRepository = Depends(),
):
    if user := user_repo.get_user_by_username(username=username):
        return UserMeResponse.model_validate(obj=user)

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
    username: str = Depends(authenticate),
    new_password: str = Body(..., embed=True),
    user_repo: UserRepository = Depends(),
):
    if user := user_repo.get_user_by_username(username=username):
        user.update_password(password=new_password)
        user_repo.save(user=user)
        return UserMeResponse.model_validate(obj=user)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )

@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
def delete_user_handler(
    username: str = Depends(authenticate),
    user_repo: UserRepository = Depends(),
):
    if user := user_repo.get_user_by_username(username=username):
        user_repo.delete(user=user)
        return

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
    _: str = Depends(authenticate),
    username: str = Path(..., max_length=10),
    session: Session = Depends(get_session),
):
    user: User | None = session.query(User).filter(User.username == username).first()
    if user:
        return UserResponse(username=user.username)

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )

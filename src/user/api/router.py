import asyncio

import httpx
from fastapi import APIRouter, Path, Body, status, HTTPException, Depends, BackgroundTasks
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from sqlalchemy.orm import Session

from config import settings
from config.cache import redis_client
from config.database.connection import get_session
from user.service.authentication import check_password, encode_access_token, authenticate
from user.service.email_service import send_otp
from user.models import User, SocialProvider
from user.service.otp_service import create_otp
from user.repository import UserRepository
from user.schema.request import SignUpRequestBody
from user.schema.response import UserMeResponse, UserResponse, JWTResponse

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

# 1) 카카오 로그인 하기 API
# - 사용자가 카카오 로그인 하려고 할 때
# - 사용자를 카카오 redirect -> 카카오에서 동의화면 보여줌
@router.get(
    "/social/kakao/login",
    status_code=status.HTTP_200_OK,
)
def kakao_social_login_handler():
    return RedirectResponse(
        "https://kauth.kakao.com/oauth/authorize"
        f"?client_id={settings.kakao_rest_api_key}"
        f"&redirect_uri={settings.kakao_redirect_url}"
        f"&response_type=code",
    )


# 2) 카카오 Callback API
# : 사용자가 인증 동의를 해서 카카오에서 사용자의 auth_code를 넘겨줄 때
@router.get(
    "/social/kakao/callback",
    status_code=status.HTTP_200_OK,
)
def kakao_social_callback_handler(
    code: str,
    user_repo: UserRepository = Depends(),
):
    # 1) auth_code -> access_token 발급받기
    response = httpx.post(
        "https://kauth.kakao.com/oauth/token",
        data={
            "grant_type": "authorization_code",
            "client_id": settings.kakao_rest_api_key,
            "redirect_uri": settings.kakao_redirect_url,
            "code": code,
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        }
    )

    response.raise_for_status()
    if response.is_success:
        # 2) access_token -> 사용자 정보 조회
        access_token: str = response.json().get("access_token")
        profile_response = httpx.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        profile_response.raise_for_status()
        if profile_response.is_success:
            # 3) 사용자 정보 -> 회원가입/로그인
            user_profile: dict = profile_response.json()

            user_subject: str = str(user_profile["id"])
            email: str = user_profile["kakao_account"]["email"]

            user: User | None = user_repo.get_user_by_social_email(
                social_provider=SocialProvider.KAKAO, email=email
            )

            # 이미 가입된 사용자 -> 로그인
            if user:
                return JWTResponse(
                    access_token=encode_access_token(username=user.username)
                )

            # 처음 소셜 로그인하는 경우
            user = User.social_signup(
                social_provider=SocialProvider.KAKAO,
                subject=user_subject,
                email=email,
            )
            user_repo.save(user=user)

            # 4) JWT 반환
            return JWTResponse(
                access_token=encode_access_token(username=user.username)
            )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Kakao social callback failed",
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

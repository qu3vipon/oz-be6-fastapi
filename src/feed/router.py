import os
import shutil
import uuid

from fastapi import APIRouter, status, Depends, UploadFile, File, Form

from feed.models import Post
from feed.repository import PostRepository
from feed.response import PostResponse, PostListResponse
from user.models import User
from user.repository import UserRepository
from user.service.authentication import authenticate

router = APIRouter(tags=["Feed"])

# 1) Post 생성
@router.post(
    "/posts",
    status_code=status.HTTP_201_CREATED,
    response_model=PostResponse,
)
def create_post_handler(
    username: str = Depends(authenticate),
    image: UploadFile = File(...),
    content: str = Form(),
    user_repo: UserRepository = Depends(),
    post_repo: PostRepository = Depends(),
):
    user: User | None = user_repo.get_user_by_username(username=username)

    # 1) image를 로컬 서버에 저장
    image_filename: str = f"{uuid.uuid4()}_{image.filename}"
    file_path = os.path.join("feed/posts", image_filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(image.file, f)

    # 2) image의 경로 & content -> Post 테이블에 저장
    new_post = Post.create(user_id=user.id, content=content, image=file_path)
    post_repo.save(post=new_post)
    return PostResponse.model_validate(obj=new_post)


# 2) Feed 조회(전체 Post 조회)(R)
#   - image, user 정보
@router.get(
    "/posts",
    status_code=status.HTTP_200_OK,
    response_model=PostListResponse,
)
def get_posts_handler(post_repo: PostRepository = Depends()):
    # 1) 전체 post 조회(created_at 역순) => 최신 게시글 순서대로 조회
    posts = post_repo.get_posts()

    # 2) 그대로 반환
    return PostListResponse.build(posts=posts)


# 3) Post 수정(U)
# 4) Post 삭제(D)
# 5) Post 상세 조회
#   - image, user 정보 + content, like_count, comment_count, comments

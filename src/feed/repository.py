from fastapi import Depends
from sqlalchemy.orm import Session, joinedload, contains_eager

from config.database.connection import get_session
from feed.models import Post, PostComment


class PostRepository:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def save(self, post: Post) -> None:
        self.session.add(post)
        self.session.commit()

    def get_posts(self):
        return self.session.query(Post).order_by(Post.created_at.desc()).all()

    def get_post(self, post_id: int) -> Post | None:
        return self.session.query(Post).filter_by(id=post_id).first()

    def get_post_detail(self, post_id: int) -> Post | None:
        return (
            self.session.query(Post)
            .filter_by(id=post_id)
            .join(Post.comments)
            .filter(PostComment.parent_id == None)  # 부모인 댓글만
            .options(
                joinedload(Post.user),
                contains_eager(Post.comments).joinedload(PostComment.replies),
            ).first()
        )

    def delete(self, post: Post) -> None:
        self.session.delete(post)
        self.session.commit()

    def delete_my_post(self, post_id: int, user_id: int) -> None:
        # 두 조건을 모두 만족하는 게시글이 있으면 삭제
        # 없으면 아무 동작도 안함
        self.session.query(Post).filter_by(id=post_id, user_id=user_id).delete()
        self.session.commit()


class PostCommentRepository:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def save(self, comment: PostComment) -> None:
        self.session.add(comment)
        self.session.commit()

    def get_comment(self, comment_id: int) -> PostComment | None:
        return self.session.query(PostComment).filter_by(id=comment_id).first()

    def delete(self, comment: PostComment) -> None:
        self.session.delete(comment)
        self.session.commit()

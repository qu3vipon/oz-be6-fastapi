# DB에 작업(생성, 조회, 수정, 삭제)
from fastapi import Depends
from sqlalchemy.orm import Session

from config.database import get_session
from user.models import User


class UserRepository:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def save(self, user: User) -> None:
        self.session.add(user)
        self.session.commit()

    def get_user_by_username(self, username: str) -> User | None:
        return self.session.query(User).filter(User.username == username).first()

    def delete(self, user: User) -> None:
        self.session.delete(user)
        self.session.commit()

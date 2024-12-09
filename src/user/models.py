import re
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime

from config.database.orm import Base
from user.authentication import hash_password


class User(Base):
    __tablename__ = "service_user"
    id = Column(Integer, primary_key=True)
    username = Column(String(16), unique=True, nullable=False)
    email = Column(String(256), nullable=True)
    password = Column(String(60), nullable=False)  # bcrypt 60자
    created_at = Column(DateTime, default=datetime.now)

    @staticmethod
    def _is_bcrypt_pattern(password: str) -> bool:
        bcrypt_pattern = r'^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$'
        return re.match(bcrypt_pattern, password) is not None

    @classmethod
    def create(cls, username: str, password: str):
        if cls._is_bcrypt_pattern(password):
            raise ValueError("Password must be plain text.")

        hashed_password = hash_password(plain_text=password)
        return cls(username=username, password=hashed_password)

    def update_password(self, password: str):
        if self._is_bcrypt_pattern(password):
            raise ValueError("Password must be plain text.")

        hashed_password = hash_password(plain_text=password)
        self.password = hashed_password

    def update_email(self, email: str):
        # email type validation
        self.email = email

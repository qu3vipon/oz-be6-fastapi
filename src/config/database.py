from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "mysql+pymysql://root:ozcoding_pw@127.0.0.1:33060/ozcoding"

engine = create_engine(DATABASE_URL)
SessionFactory = sessionmaker(
    bind=engine, autocommit=False, autoflush=False, expire_on_commit=False
)

Base = declarative_base()

def get_session():
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()

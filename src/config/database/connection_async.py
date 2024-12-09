from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

DATABASE_URL = "mysql+aiomysql://root:ozcoding_pw@127.0.0.1:33060/ozcoding"

async_engine = create_async_engine(DATABASE_URL)
AsyncSessionFactory = async_sessionmaker(
    bind=async_engine, autocommit=False, autoflush=False, expire_on_commit=False
)

async def get_async_session():
    session = AsyncSessionFactory()
    try:
        yield session
    finally:
        await session.close()  # db에 커넥션 종료

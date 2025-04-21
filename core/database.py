from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_DATABASE_URI = 'sqlite+aiosqlite:///./database.db'


def create_engine_and_session():
    try:
        engine_ = create_async_engine(SQLALCHEMY_DATABASE_URI, future=True, echo=False)
    except Exception as e:
        print(f"数据库连接失败 {e}")
        raise e

    # 创建异步数据库会话
    db_session_ = async_sessionmaker(autocommit=False, autoflush=False, bind=engine_, expire_on_commit=False)
    return engine_, db_session_


engine, db_session = create_engine_and_session()


async def get_db():
    session = db_session()
    try:
        yield session
    except Exception as e:
        await session.rollback()
        raise e
    finally:
        await session.close()


# 创建基础模型和初始化数据库
BaseModel = declarative_base()


async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(BaseModel.metadata.create_all)
        print("数据库初始化完成")
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        print("Error: 数据库初始化失败")

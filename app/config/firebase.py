import firebase_admin
from firebase_admin import credentials, firestore, auth
from app.config.settings import settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import logging

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,

    future=True,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
    echo=False
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for models
Base = declarative_base()

# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Initialize database tables
async def init_db():
    async with engine.begin() as conn:
         await conn.run_sync(Base.metadata.create_all)
    #    await conn.run_sync(Base.metadata.drop_all)
        
# def initialize_firebase():

#     """Initialize Firebase Admin SDK"""
#     if not firebase_admin._apps:
#         cred = credentials.Certificate(settings.GoogleServiceAccount)
#         firebase_admin.initialize_app(cred)
#     return firestore.client()

# db = initialize_firebase()


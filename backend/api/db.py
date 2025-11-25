"""
Database Connection Management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from api.config import settings
from loguru import logger

# Create database engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Check connection before using
    pool_size=10,        # Connection pool size
    max_overflow=20,     # Max extra connections
    echo=settings.DEBUG, # Print SQL statements in debug mode
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()


def get_db() -> Session:
    """
    Get database session dependency function

    Usage example:
    ```python
    from fastapi import Depends
    from api.db import get_db

    @app.get("/")
    def read_root(db: Session = Depends(get_db)):
        # Use db to perform database operations
        pass
    ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database
    - Create all tables
    - Create default administrator account
    """
    # Import all models to register them (required for table creation)
    from models import (
        User,
        Document,
        Folder,
        Chunk,
        ACL,
        ACLRule,
        QueryLog,
        OperationLog,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")

    # Create default administrator account
    from models.user_models import UserRole
    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    db = SessionLocal()
    try:
        # Check if admin user already exists
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@docsagent.com",
                hashed_password=pwd_context.hash("admin123"),  # Default password: admin123
                full_name="System Administrator",
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)
            db.commit()
            logger.info("Created default admin user - username: admin, password: admin123")
        else:
            logger.info("Admin user already exists, skipping creation")
    except Exception as e:
        logger.error(f"Failed to create default admin user: {e}")
        db.rollback()
    finally:
        db.close()


def drop_all_tables():
    """
    Drop all tables (dangerous operation, only use in development mode)
    """
    if not settings.DEBUG:
        logger.error("Cannot drop tables in production mode")
        return

    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables have been dropped")


if __name__ == "__main__":
    # Test database connection
    from api.logging_config import setup_logging

    setup_logging()
    logger.info(f"Database URL: {settings.database_url}")

    # Initialize database
    init_db()

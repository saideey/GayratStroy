"""
Database connection and session management.
"""

import os
from contextlib import contextmanager
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool

from .base import Base


class DatabaseConnection:
    """Database connection manager."""
    
    _instance = None
    _engine = None
    _session_factory = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._engine is None:
            self._initialize()
    
    def _initialize(self):
        """Initialize database connection."""
        database_url = os.getenv(
            'DATABASE_URL',
            'postgresql://postgres:postgres@db:5432/metall_basa'
        )
        
        # Use NullPool in production to avoid stale connections
        # Each request gets a fresh connection
        use_null_pool = os.getenv('USE_NULL_POOL', 'true').lower() == 'true'
        
        if use_null_pool:
            # NullPool - no connection pooling, each request opens new connection
            # More reliable but slightly slower
            self._engine = create_engine(
                database_url,
                poolclass=NullPool,
                connect_args={
                    "connect_timeout": 10,
                    "options": "-c statement_timeout=30000"
                },
                echo=os.getenv('SQL_ECHO', 'false').lower() == 'true'
            )
            print("✅ Database initialized with NullPool (no connection pooling)")
        else:
            # QueuePool with aggressive recycling
            self._engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=3,
                max_overflow=5,
                pool_pre_ping=True,
                pool_recycle=60,  # Recycle every 60 seconds
                pool_timeout=10,
                connect_args={
                    "connect_timeout": 10,
                    "keepalives": 1,
                    "keepalives_idle": 10,
                    "keepalives_interval": 5,
                    "keepalives_count": 3,
                },
                echo=os.getenv('SQL_ECHO', 'false').lower() == 'true'
            )
            print("✅ Database initialized with QueuePool")
        
        self._session_factory = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
    
    @property
    def engine(self):
        """Get database engine."""
        return self._engine
    
    @property
    def session_factory(self):
        """Get session factory."""
        return self._session_factory
    
    def create_all_tables(self):
        """Create all tables in the database."""
        from .models import (
            user, product, warehouse, sale, 
            customer, supplier, finance, settings
        )
        Base.metadata.create_all(self._engine)
    
    def drop_all_tables(self):
        """Drop all tables in the database."""
        Base.metadata.drop_all(self._engine)
    
    @contextmanager
    def get_session(self) -> Session:
        """Get database session with automatic commit/rollback."""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_session_direct(self) -> Session:
        """Get database session without context manager."""
        return self._session_factory()
    
    def dispose_engine(self):
        """Dispose all pooled connections."""
        if self._engine:
            self._engine.dispose()
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print(f"❌ Database connection test failed: {e}")
            return False


# Singleton instance
db = DatabaseConnection()


def get_db() -> Session:
    """Dependency for FastAPI to get database session."""
    session = db.get_session_direct()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Initialize database and create all tables."""
    db.create_all_tables()
    print("✅ Database tables created successfully!")


def reset_db():
    """Reset database - drop and recreate all tables."""
    db.drop_all_tables()
    db.create_all_tables()
    print("✅ Database reset successfully!")

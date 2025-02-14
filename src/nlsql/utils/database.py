from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from typing import Optional
from ..core.config import get_settings

class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self):
        self.settings = get_settings()
        self._engine: Optional[Engine] = None
        self._session_factory = None
    
    @property
    def engine(self) -> Engine:
        """Get SQLAlchemy engine, creating it if necessary."""
        if self._engine is None:
            self._engine = create_engine(
                self.settings.DATABASE_URL,
                pool_size=self.settings.DB_POOL_SIZE,
                max_overflow=self.settings.DB_MAX_OVERFLOW,
                pool_pre_ping=True
            )
        return self._engine
    
    @property
    def session_factory(self):
        """Get session factory, creating it if necessary."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
        return self._session_factory
    
    def get_session(self):
        """Get a new database session."""
        return self.session_factory()
    
    def dispose(self):
        """Dispose of the engine and all connections."""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None

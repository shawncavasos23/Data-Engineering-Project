from sqlalchemy import create_engine, event # type: ignore
from sqlalchemy.engine import Engine # type: ignore
import logging

def create_sqlalchemy_engine(db_path: str = "trading_data.db") -> Engine:
    """
    Create a SQLAlchemy engine for the SQLite database with foreign key support.

    Parameters:
        db_path (str): Path to the SQLite database file.

    Returns:
        Engine: SQLAlchemy engine object.
    """
    try:
        engine = create_engine(f"sqlite:///{db_path}", echo=False)

        # Enable foreign key constraints for SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        logging.debug(f"SQLAlchemy engine created for {db_path}")
        return engine

    except Exception as e:
        logging.error(f"Failed to create SQLAlchemy engine: {e}")
        raise

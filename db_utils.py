from sqlalchemy import create_engine, event  # type: ignore
from sqlalchemy.engine import Engine  # type: ignore
import logging
import os

def create_sqlalchemy_engine(
    db_type: str = "sqlite",
    db_path: str = "trading_data.db",
    username: str = None,
    password: str = None,
    host: str = "localhost",
    port: int = 5432,
    dbname: str = None,
    echo: bool = False,
    timeout: int = 30
) -> Engine:
    """
    Create a SQLAlchemy engine with support for SQLite and PostgreSQL.
    
    Parameters:
        db_type (str): Database type: 'sqlite' (default) or 'postgres'.
        db_path (str): SQLite DB file path (only used if db_type='sqlite').
        username (str): Username for PostgreSQL (required if db_type='postgres').
        password (str): Password for PostgreSQL (required if db_type='postgres').
        host (str): Host for PostgreSQL.
        port (int): Port for PostgreSQL.
        dbname (str): Database name for PostgreSQL.
        echo (bool): Whether to enable SQLAlchemy echo/debug output.
        timeout (int): Timeout in seconds for SQLite connection.

    Returns:
        Engine: Configured SQLAlchemy engine.
    """
    try:
        if db_type == "sqlite":
            engine = create_engine(f"sqlite:///{db_path}", echo=echo, connect_args={"timeout": timeout})

            @event.listens_for(engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

            logging.debug(f"SQLite engine created for {db_path} with timeout={timeout} seconds")

        elif db_type == "postgres":
            if not all([username, password, dbname]):
                raise ValueError("PostgreSQL requires username, password, and dbname")

            engine = create_engine(
                f"postgresql://{username}:{password}@{host}:{port}/{dbname}",
                echo=echo
            )
            logging.debug(f"PostgreSQL engine created for {dbname}@{host}:{port}")

        else:
            raise ValueError(f"Unsupported database type: {db_type}")

        return engine

    except Exception as e:
        logging.error(f"Failed to create SQLAlchemy engine: {e}")
        raise


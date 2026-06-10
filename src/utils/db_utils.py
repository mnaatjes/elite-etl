import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

def ping_database() -> tuple[bool, str]:
    """
    Attempts to connect to the database using credentials from .env.
    Returns (Success: bool, Message: str)
    """
    load_dotenv()
    
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    
    db_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}"
    
    engine = create_engine(db_url, connect_args={'connect_timeout': 3})
    
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, "Database is online and reachable."
    except OperationalError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

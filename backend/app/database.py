
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()


def create_database_engine(env_name):
    database_url = os.getenv(env_name)

    if not database_url:
        raise RuntimeError(
            f"{env_name} is missing from backend/.env"
        )

    return create_engine(
        database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 5},
    )


# Existing connection for dashboard endpoints
engine = create_database_engine("DATABASE_URL")

# Read-only connection for AI-generated SQL
ai_engine = create_database_engine("AI_DATABASE_URL")

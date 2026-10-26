
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, Field
from fastapi.encoders import jsonable_encoder
import socket

from app.ai_service import generate_sql
from app.sql_validator import validate_sql, SQLValidationError
from app.database import engine
from app.connections import (
    router as connections_router,
    MySQLConnectionRequest,
    validate_connection_details,
    build_mysql_engine,
)

app = FastAPI(
    title="QueryPilot AI",
    description="AI-powered manufacturing data analyst",
    version="1.0.0",
)

app.include_router(connections_router)


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    connection: MySQLConnectionRequest


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


@app.get("/")
def home():
    return {"message": "Welcome to QueryPilot AI"}


@app.get("/api/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
        }

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Database connection failed",
        )


@app.get("/api/overview")
def overview():
    query = text("""
        SELECT
            COUNT(*) AS total_machines,
            SUM(
                CASE
                    WHEN machine_failure = TRUE THEN 1
                    ELSE 0
                END
            ) AS failures,
            ROUND(AVG(torque_nm), 2) AS average_torque_nm,
            ROUND(AVG(tool_wear_min), 2)
                AS average_tool_wear_min
        FROM machine_data
    """)

    try:
        with engine.connect() as connection:
            result = connection.execute(query).mappings().one()
            return dict(result)

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve manufacturing summary",
        )


@app.get("/api/records")
def records(limit: int = Query(default=10, ge=1, le=100)):
    query = text("""
        SELECT
            machine_id,
            product_type,
            production_date,
            rotational_speed_rpm,
            torque_nm,
            tool_wear_min,
            machine_failure
        FROM machine_data
        ORDER BY production_date DESC, machine_id DESC
        LIMIT :limit
    """)

    try:
        with engine.connect() as connection:
            result = connection.execute(
                query, {"limit": limit}
            ).mappings().all()

            return [dict(row) for row in result]

    except SQLAlchemyError:
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve machine records",
        )


@app.post("/api/ask")
def ask_question(request: AskRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Please enter a question.",
        )

    # Step 1: Validate the user's database connection details.
    validate_connection_details(request.connection)

    user_engine = None

    try:
        connection_details = request.connection

        # Step 2: Create a temporary engine using verified TLS.
        user_engine = build_mysql_engine(connection_details)

        # Step 3: Discover the user's database schema.
        inspector = inspect(user_engine)
        table_names = sorted(inspector.get_table_names())

        if not table_names:
            raise HTTPException(
                status_code=400,
                detail="No tables were found in this database.",
            )

        if len(table_names) > 50:
            raise HTTPException(
                status_code=400,
                detail=(
                    "This database has too many tables "
                    "for this prototype."
                ),
            )

        schema = []

        for table_name in table_names:
            columns = inspector.get_columns(table_name)

            if len(columns) > 100:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "A table has too many columns "
                        "for this prototype."
                    ),
                )

            schema.append({
                "table": table_name,
                "columns": [
                    {
                        "name": column["name"],
                        "type": str(column["type"]),
                    }
                    for column in columns
                ],
            })

        # Step 4: Generate SQL using the discovered schema.
        try:
            generated_sql = generate_sql(question, schema)
        except Exception:
            raise HTTPException(
                status_code=502,
                detail="The AI service could not generate a query.",
            )

        # Step 5: Validate the generated SQL.
        try:
            safe_sql = validate_sql(
                generated_sql,
                allowed_tables=set(table_names),
            )
        except SQLValidationError:
            raise HTTPException(
                status_code=400,
                detail=(
                    "The generated query did not pass "
                    "safety validation."
                ),
            )

        # Step 6: Execute the validated query.
        with user_engine.connect() as connection:
            connection.exec_driver_sql(
                "SET SESSION max_execution_time = 3000"
            )

            result = connection.execute(text(safe_sql))

            columns = list(result.keys())
            rows = [
                dict(row)
                for row in result.mappings().fetchmany(101)
            ]

            rows = rows[:100]

        return jsonable_encoder({
            "question": question,
            "sql": safe_sql,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "database": connection_details.database,
        })

    except HTTPException:
        raise

    except (SQLAlchemyError, socket.timeout):
        raise HTTPException(
            status_code=400,
            detail=(
                "The database could not complete the request. "
                "Check the connection details, permissions, "
                "network access, and TLS configuration."
            ),
        )

    finally:
        if user_engine is not None:
            user_engine.dispose()


import ipaddress
import os
import re
import socket
import ssl
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, SecretStr
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError

router = APIRouter(
    prefix="/api/connections",
    tags=["Database connections"],
)


class MySQLConnectionRequest(BaseModel):
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(default=3306, ge=1, le=65535)
    database: str = Field(min_length=1, max_length=64)
    username: str = Field(min_length=1, max_length=128)
    password: SecretStr


def validate_remote_host(host: str) -> str:
    """Validate a public hostname or globally routable IP address."""
    host = host.strip()

    if not host:
        raise HTTPException(
            status_code=400,
            detail="A database host is required.",
        )

    if any(char in host for char in "/\\@?#"):
        raise HTTPException(
            status_code=400,
            detail="Enter a hostname or IP address, not a URL.",
        )

    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None

    if ip is not None:
        if not ip.is_global:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Private, loopback, and reserved IP addresses "
                    "are not allowed."
                ),
            )
        return host

    hostname = host.rstrip(".")

    if len(hostname) > 253:
        raise HTTPException(
            status_code=400,
            detail="The database hostname is too long.",
        )

    labels = hostname.split(".")

    if len(labels) < 2 or any(
        not label
        or len(label) > 63
        or not re.fullmatch(
            r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?",
            label,
        )
        for label in labels
    ):
        raise HTTPException(
            status_code=400,
            detail="Enter a valid public database hostname.",
        )

    # Initial SSRF protection. This alone does not prevent DNS rebinding.
    try:
        addresses = socket.getaddrinfo(
            hostname,
            None,
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror:
        raise HTTPException(
            status_code=400,
            detail="The database hostname could not be resolved.",
        )

    resolved_ips = set()

    for address in addresses:
        try:
            resolved_ips.add(ipaddress.ip_address(address[4][0]))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="The database hostname resolved to an invalid IP address.",
            )

    if not resolved_ips or any(
        not resolved_ip.is_global for resolved_ip in resolved_ips
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "The database hostname must resolve only "
                "to public IP addresses."
            ),
        )

    return hostname


def validate_connection_details(
    request: MySQLConnectionRequest,
) -> None:
    """Validate the submitted MySQL connection details."""
    validate_remote_host(request.host)

    if not 1 <= request.port <= 65535:
        raise HTTPException(
            status_code=400,
            detail="Enter a valid database port between 1 and 65535.",
        )

    if not re.fullmatch(r"[A-Za-z0-9_]+", request.database):
        raise HTTPException(
            status_code=400,
            detail=(
                "Database name may contain only letters, "
                "numbers, and underscores."
            ),
        )

    if not request.username.strip():
        raise HTTPException(
            status_code=400,
            detail="Username cannot be empty.",
        )

    if not request.password.get_secret_value():
        raise HTTPException(
            status_code=400,
            detail="Password cannot be empty.",
        )


def build_mysql_engine(request: MySQLConnectionRequest):
    """Build a MySQL engine with verified TLS."""
    backend_dir = Path(__file__).resolve().parent.parent

    ca_setting = os.getenv("MYSQL_SSL_CA", "").strip()
    tls_context = ssl.create_default_context()

    if ca_setting:
        ca_file = Path(ca_setting).expanduser()

        if not ca_file.is_absolute():
            ca_file = backend_dir / ca_file

        if not ca_file.is_file():
            raise RuntimeError(
                "The configured MySQL CA certificate was not found. "
                "Check MYSQL_SSL_CA and verify the file path."
            )

        tls_context.load_verify_locations(cafile=str(ca_file))

    tls_context.verify_mode = ssl.CERT_REQUIRED
    tls_context.check_hostname = True

    url = URL.create(
        drivername="mysql+pymysql",
        username=request.username,
        password=request.password.get_secret_value(),
        host=request.host.strip().rstrip("."),
        port=request.port,
        database=request.database,
    )

    return create_engine(
        url,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={
            "connect_timeout": 5,
            "ssl": tls_context,
        },
    )


@router.post("/test")
def test_mysql_connection(request: MySQLConnectionRequest):
    validate_connection_details(request)

    user_engine = None

    try:
        user_engine = build_mysql_engine(request)

        # Verify that the database connection works.
        with user_engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        # Discover available tables.
        inspector = inspect(user_engine)
        table_names = sorted(inspector.get_table_names())

        if len(table_names) > 50:
            raise HTTPException(
                status_code=400,
                detail=(
                    "This database has more than 50 tables. "
                    "Select a smaller database for this prototype."
                ),
            )

        schema = []

        for table_name in table_names:
            columns = inspector.get_columns(table_name)

            if len(columns) > 100:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "A table has more than 100 columns; "
                        "schema discovery was stopped."
                    ),
                )

            schema.append({
                "table": table_name,
                "columns": [
                    {
                        "name": column["name"],
                        "type": str(column["type"]),
                        "nullable": column.get("nullable", True),
                    }
                    for column in columns
                ],
            })

        return {
            "status": "connected",
            "database": request.database,
            "table_count": len(schema),
            "schema": schema,
        }

    except HTTPException:
        raise

    except (SQLAlchemyError, OSError, ssl.SSLError) as exc:
        # Log the exception type only, not the raw message.
        print(
            f"MySQL connection test failed: {type(exc).__name__}"
        )

        raise HTTPException(
            status_code=400,
            detail=(
                "Could not connect securely to this MySQL database. "
                "Check the host, port, database name, credentials, "
                "network access, and TLS certificate configuration."
            ),
        )

    finally:
        if user_engine is not None:
            user_engine.dispose()

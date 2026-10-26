
import sqlglot
from sqlglot import exp


MAX_ROWS = 100


class SQLValidationError(ValueError):
    """Raised when generated SQL does not meet safety rules."""


def validate_sql(
    sql: str,
    allowed_tables: set[str] | None = None,
) -> str:
    if not sql or not sql.strip():
        raise SQLValidationError("The SQL query is empty.")

    # Require an explicit allowlist for the connected database.
    if not allowed_tables:
        raise SQLValidationError(
            "No allowed database tables were provided."
        )

    # Normalize table names for case-insensitive comparison.
    allowed_tables = {
        table_name.lower() for table_name in allowed_tables
    }

    try:
        statements = sqlglot.parse(sql, read="mysql")
    except sqlglot.errors.ParseError as exc:
        raise SQLValidationError(
            "The SQL syntax is invalid."
        ) from exc

    # Reject multiple statements.
    statements = [
        statement for statement in statements
        if statement is not None
    ]

    if len(statements) != 1:
        raise SQLValidationError(
            "Only one SQL statement is allowed."
        )

    tree = statements[0]

    # Only a SELECT statement is permitted.
    if not isinstance(tree, exp.Select):
        raise SQLValidationError(
            "Only SELECT queries are allowed."
        )

    # Check every table reference, including references in subqueries.
    tables = list(tree.find_all(exp.Table))

    if not tables:
        raise SQLValidationError(
            "The query must reference an allowed database table."
        )

    for table in tables:
        # Disallow database-qualified and catalog-qualified names.
        if table.db or table.catalog:
            raise SQLValidationError(
                "Database-qualified table names are not allowed."
            )

        if table.name.lower() not in allowed_tables:
            raise SQLValidationError(
                f"Table '{table.name}' is not allowed."
            )

    # Keep the initial version simple: no joins or nested queries.
    if tree.args.get("joins"):
        raise SQLValidationError(
            "JOIN operations are not allowed yet."
        )

    if list(tree.find_all(exp.Subquery)):
        raise SQLValidationError(
            "Nested queries are not allowed yet."
        )

    # Prevent SELECT INTO and locking clauses.
    if list(tree.find_all(exp.Into)):
        raise SQLValidationError(
            "SELECT INTO is not allowed."
        )

    if list(tree.find_all(exp.Lock)):
        raise SQLValidationError(
            "Locking clauses are not allowed."
        )

    # Require an explicit LIMIT and enforce the maximum.
    limit = tree.args.get("limit")

    if limit is None or limit.expression is None:
        raise SQLValidationError(
            f"A LIMIT of at most {MAX_ROWS} is required."
        )

    limit_expression = limit.expression

    if not isinstance(limit_expression, exp.Literal):
        raise SQLValidationError(
            "LIMIT must be a numeric constant."
        )

    if limit_expression.is_string:
        raise SQLValidationError(
            "LIMIT must be numeric."
        )

    try:
        row_limit = int(limit_expression.this)
    except (TypeError, ValueError) as exc:
        raise SQLValidationError(
            "LIMIT must be a whole number."
        ) from exc

    if row_limit < 1 or row_limit > MAX_ROWS:
        raise SQLValidationError(
            f"LIMIT must be between 1 and {MAX_ROWS}."
        )

    # Return normalized MySQL SQL only after all checks pass.
    return tree.sql(dialect="mysql")

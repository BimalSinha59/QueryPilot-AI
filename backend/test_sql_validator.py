
from app.sql_validator import validate_sql, SQLValidationError


valid_query = """
SELECT
    product_type,
    100.0 * SUM(
        CASE WHEN machine_failure = TRUE THEN 1 ELSE 0 END
    ) / NULLIF(COUNT(*), 0) AS failure_rate
FROM machine_data
GROUP BY product_type
ORDER BY failure_rate DESC
LIMIT 1;
"""

print("Testing valid query:")
print(validate_sql(valid_query))
print("\nValid query accepted.")


unsafe_queries = [
    "DELETE FROM machine_data",
    "SELECT * FROM users LIMIT 10",
    "SELECT * FROM machine_data",
    "SELECT * FROM machine_data LIMIT 1000",
    "SELECT * FROM machine_data LIMIT 5; DELETE FROM machine_data",
]

print("\nTesting unsafe queries:")

for query in unsafe_queries:
    try:
        validate_sql(query)
        print("UNEXPECTEDLY ACCEPTED:", query)
    except SQLValidationError as exc:
        print("Rejected:", str(exc))


from app.ai_service import generate_sql

question = "Which product type has the highest machine failure rate?"

sql = generate_sql(question)

print("\nUser question:")
print(question)

print("\nGenerated SQL:")
print(sql)

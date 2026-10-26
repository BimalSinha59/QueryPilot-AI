
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError("GROQ_API_KEY is missing from backend/.env")

client = Groq(api_key=api_key)

MODEL_NAME = "openai/gpt-oss-20b"


def generate_sql(question: str, schema: list[dict]) -> str:
    schema_description = []

    for table in schema:
        columns = ", ".join(
            f"{column['name']} ({column['type']})"
            for column in table["columns"]
        )

        schema_description.append(
            f"Table: {table['table']}\nColumns: {columns}"
        )

    schema_text = "\n\n".join(schema_description)

    prompt = f"""
You are a MySQL SQL query generator.

The user asks a question about their database.
Generate one MySQL SELECT query that answers it.

Available database schema:
{schema_text}

Rules:
- Use only the tables and columns listed above.
- Generate exactly one SELECT query.
- Do not generate INSERT, UPDATE, DELETE, DROP, ALTER,
  CREATE, TRUNCATE, or other modification statements.
- Do not use SELECT *.
- Do not include markdown fences or explanations.
- Do not assume columns that are not listed.
- Add a LIMIT of 100 or less.

User question:
{question}
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0,
    )

    return response.choices[0].message.content.strip()


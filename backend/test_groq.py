
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError("GROQ_API_KEY is missing from backend/.env")

client = Groq(api_key=api_key)

response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {
            "role": "system",
            "content": (
                "You are QueryPilot AI, a manufacturing data analyst. "
                "Answer clearly and briefly."
            ),
        },
        {
            "role": "user",
            "content": (
                "Explain in one sentence what a machine failure rate means."
            ),
        },
    ],
    max_completion_tokens=150,
)

print("Groq API connected successfully!")
print("Model response:")
print(response.choices[0].message.content)

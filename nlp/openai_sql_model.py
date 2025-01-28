# nlp/openai_sql_model.py
import openai
from server.config import settings

openai.api_key = settings.OPENAI_API_KEY

def openai_generate_sql(prompt: str) -> str:
    messages = [
        {"role": "system", "content": "You are an expert SQL generator. Return only valid SQL."},
        {"role": "user", "content": prompt}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # or "gpt-4"
        messages=messages,
        max_tokens=200,
        temperature=0.0
    )
    return response.choices[0].message["content"].strip()

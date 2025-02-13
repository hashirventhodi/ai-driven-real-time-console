# nlp/openai_sql_model.py
import openai
from server.config import settings

openai.api_key = settings.OPENAI_API_KEY

def openai_generate_sql(messages) -> str:
    """
    Expects a list of messages:
      [
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."}
      ]
    Returns the raw text output from OpenAI.
    """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # or gpt-4
        messages=messages,
        max_tokens=256,
        temperature=0.0
    )
    return response.choices[0]["message"]["content"].strip()

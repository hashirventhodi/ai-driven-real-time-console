# nlp/query_understanding.py
from typing import Tuple, Dict, List
from .schema_encoder import encode_database_schema
from .advanced_features.query_optimization import optimize_sql_query
from .advanced_features.data_validation import validate_sql_query

# Option A: Hugging Face
from .hf_sql_model import HFSQLModel
hf_model = HFSQLModel()

# Option B: OpenAI
from .openai_sql_model import openai_generate_sql

def process_natural_language_query(
    query_text: str,
    db,
    metadata,
    conversation_history: List[str] = None,
    use_openai: bool = False
) -> Tuple[str, Dict]:
    """
    Convert NL query (+ conversation) into SQL. Summarize large schemas if needed.
    """
    # 1. Build conversation context
    combined_context = build_combined_context(query_text, conversation_history)

    # 2. Summarize / chunk schema 
    schema_text = encode_database_schema(metadata, max_token_budget=512)

    # 3. Build final prompt for LLM
    prompt = (
        f"Conversation:\n{combined_context}\n\n"
        f"Database Schema:\n{schema_text}\n\n"
        "Return a valid SQL query only."
    )

    # 4. Generate SQL
    if use_openai:
        generated_sql = openai_generate_sql(prompt)
    else:
        generated_sql = hf_model.generate_sql(prompt)

    # 5. Validate & Optimize
    validate_sql_query(generated_sql, metadata)
    optimized_sql = optimize_sql_query(generated_sql, db, metadata)

    # 6. Determine chart info
    chart_info = extract_chart_info(query_text)
    return optimized_sql, chart_info

def build_combined_context(query_text: str, conversation_history: List[str]) -> str:
    if not conversation_history:
        conversation_history = []
    last_messages = "\n".join(conversation_history[-5:])
    return f"{last_messages}\nUser Query: {query_text}"

def extract_chart_info(query_text: str) -> Dict:
    query_lower = query_text.lower()
    if "trend" in query_lower:
        return {"type": "line", "x": "date", "y": "sales"}
    elif "distribution" in query_lower:
        return {"type": "pie", "x": "category", "y": "count"}
    elif "bar chart" in query_lower:
        return {"type": "bar", "x": "some_dimension", "y": "some_metric"}
    # fallback
    return {}

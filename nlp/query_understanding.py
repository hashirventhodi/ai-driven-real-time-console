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
    print("process_natural_language_query")
    """
    Convert NL -> SQL using improved prompt engineering:
    1) Build a minimal conversation context (avoid repeated lines).
    2) Summarize/encode large schemas.
    3) Force model to output ONLY the SQL.
    4) Post-process to strip fluff if needed.
    """
    # 1. Build a minimal conversation context 
    #    (We skip repeated "User Query:" lines).
    combined_context = build_combined_context(query_text, conversation_history)
    
    # 2. Summarize / chunk schema 
    schema_text = encode_database_schema(metadata, max_token_budget=300)
    
    # 3. Build final text that the 'user' role will see
    #    Notice we ask explicitly: "Return ONLY a valid SQL query."
    
    user_content = f"""
        Here is the current conversation context (truncated as needed):
        {combined_context}

        Database Schema (possibly truncated):
        {schema_text}

        IMPORTANT INSTRUCTION:
        You MUST output ONLY a valid SQL statement. No additional text or explanation.
        """
        
    if use_openai:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert SQL assistant. "
                    "You must return ONLY a valid SQL query, with no extra text."
                )
            },
            {
                "role": "user",
                "content": user_content
            }
        ]
        # Call OpenAI (see openai_sql_model.py)
        raw_output = openai_generate_sql(messages)
    else:
        # If using Hugging Face T5 or GPT-2 style,
        # you'd just build a prompt string and call hf_model.generate_sql(prompt).
        prompt = (
            "SYSTEM: You are an expert SQL assistant. Return only SQL.\n\n"
            f"{user_content}"
        )
        print("Prompt for SQL Generation:\n", prompt)

        raw_output = hf_model.generate_sql(prompt)
        # raise NotImplementedError("HF approach not shown here. Implement similarly.")

    # 4. Optional: post-process to ensure we only have SQL
    generated_sql = extract_sql_command(raw_output)
        
    # prompt = (
    #     f"Conversation:\n{combined_context}\n\n"
    #     f"Database Schema:\n{schema_text}\n\n"
    #     "Return a valid SQL query only."
    # )


    # # 4. Generate SQL
    # if use_openai:
    #     generated_sql = openai_generate_sql(prompt)
    # else:
    #     generated_sql = hf_model.generate_sql(prompt)

    # 5. Validate & Optimize
    validate_sql_query(generated_sql, metadata)
    optimized_sql = optimize_sql_query(generated_sql, db, metadata)

    # 6. Determine chart info
    chart_info = extract_chart_info(query_text)
    return optimized_sql, chart_info

def build_combined_context(
    current_query: str,
    conversation_history: List[str],
    max_messages: int = 3
) -> str:
    """
    Combine the last few messages, ignoring repeated identical lines 
    that might confuse the LLM.
    """
    if not conversation_history:
        conversation_history = []

    # Deduplicate or remove repeated lines if they are identical
    filtered_history = []
    for msg in reversed(conversation_history):
        if msg not in filtered_history:
            filtered_history.append(msg)
        # If it's repeated text, skip
    # We'll then take the last `max_messages` from the filtered reversed list
    filtered_history = list(reversed(filtered_history))[-max_messages:]

    history_text = "\n".join(filtered_history)
    # Add current user query
    combined = f"{history_text}\nUser Query: {current_query}"
    return combined.strip()

def extract_sql_command(raw_output: str) -> str:
    """
    Attempt to parse the LLM's response and extract only the SQL statement.
    Naive example: look for a line starting with SELECT/INSERT/UPDATE/DELETE.
    """
    import re

    # One naive approach: search for keywords at start
    pattern = r"(SELECT|INSERT|UPDATE|DELETE)\s.+"
    match = re.search(pattern, raw_output, flags=re.IGNORECASE | re.DOTALL)
    if match:
        sql = match.group(0).strip()
        return sql
    else:
        # fallback: maybe the entire raw_output is the query
        # or we raise an error
        lower_out = raw_output.lower().strip()
        if lower_out.startswith("select") or lower_out.startswith("insert") \
           or lower_out.startswith("update") or lower_out.startswith("delete"):
            return raw_output.strip()

    raise ValueError(f"Model output didn't contain a recognizable SQL command. Output:\n{raw_output}")


def extract_chart_info(query_text: str) -> Dict:
    """
    Example for detecting chart type from the user query.
    """
    query_lower = query_text.lower()
    if "trend" in query_lower:
        return {"type": "line", "x": "date", "y": "sales"}
    elif "distribution" in query_lower:
        return {"type": "pie", "x": "category", "y": "count"}
    elif "bar chart" in query_lower:
        return {"type": "bar", "x": "some_dimension", "y": "some_metric"}
    # fallback
    return {}

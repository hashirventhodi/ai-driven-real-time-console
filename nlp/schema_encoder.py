# nlp/schema_encoder.py
from sqlalchemy import inspect
from transformers import T5Tokenizer

tokenizer = T5Tokenizer.from_pretrained("t5-small")

def encode_database_schema(metadata, max_token_budget=512):
    """
    Retrieve table & column info, build textual summary, and chunk/summarize if needed.
    :param max_token_budget: maximum tokens to allocate for the schema part of the prompt.
    """
    table_names = metadata.get_table_names()
    schema_lines = []
    for table_name in table_names:
        columns = metadata.get_columns(table_name)
        col_names = [c['name'] for c in columns]
        line = f"Table {table_name}: columns = {col_names}"
        schema_lines.append(line)

    # Combine into a single text
    schema_text = "\n".join(schema_lines)

    # Check token length
    tokens = tokenizer.encode(schema_text)
    if len(tokens) <= max_token_budget:
        # It's within limit, return full
        return schema_text
    else:
        # If the schema is too large, we can do a naive truncation or summarization
        # Let's do naive chunking + placeholders

        # Example approach: 
        # 1. Sort lines by "importance" if you want, or just chunk them 
        # 2. We'll just keep as many lines as fit into the token budget and then say "Truncated..."

        truncated_lines = []
        running_tokens = 0
        for line in schema_lines:
            line_tokens = tokenizer.encode(line)
            if running_tokens + len(line_tokens) < max_token_budget - 20:  # buffer
                truncated_lines.append(line)
                running_tokens += len(line_tokens)
            else:
                truncated_lines.append("...Truncated due to large schema...")
                break
        
        return "\n".join(truncated_lines)

import re

def extract_sql(generated_text: str) -> str:
    """
    Extracts SQL code from a markdown code block.
    If the text is wrapped in ```sql ... ``` markers, this function extracts and returns
    the SQL code. Otherwise, it returns the full text stripped.
    """
    pattern = r"```sql\s*(.*?)\s*```"
    match = re.search(pattern, generated_text, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return generated_text.strip()
# nlp/advanced_features/data_validation.py
def validate_sql_query(sql_query: str, metadata):
    forbidden = ["DROP ", "DELETE ", ";", "--", "/*", "xp_"]
    if any(frag.lower() in sql_query.lower() for frag in forbidden):
        raise ValueError("Potentially dangerous query detected!")
    return True

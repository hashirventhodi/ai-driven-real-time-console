from transformers import T5Tokenizer, T5ForConditionalGeneration
import sys

def test_sql_generation():
    """
    Test the SQL generation pipeline with a simple example
    """
    print("Starting SQL generation test...")
    
    try:
        # Initialize model and tokenizer
        print("Loading T5 model and tokenizer...")
        model_name = "t5-small"
        tokenizer = T5Tokenizer.from_pretrained(model_name)
        model = T5ForConditionalGeneration.from_pretrained(model_name)
        
        # Test schema and query
        schema = """
        Table users: columns = [id, username, email]
        Table orders: columns = [id, user_id, total_amount, order_date]
        """
        
        query = "Find all users who made orders over $100"
        
        # Create prompt
        prompt = f"""
        Database Schema:
        {schema}
        
        User Query: {query}
        
        IMPORTANT: Return ONLY a valid SQL query without any additional text.
        Expected format: SELECT ... FROM ... WHERE ...
        """
        
        print("\nInput prompt:", prompt)
        
        # Tokenize
        print("\nTokenizing input...")
        input_ids = tokenizer.encode(prompt, return_tensors="pt")
        
        # Generate
        print("\nGenerating SQL...")
        outputs = model.generate(
            input_ids=input_ids,
            max_length=128,
            num_beams=4,
            temperature=0.7,
            early_stopping=True,
            no_repeat_ngram_size=2
        )
        
        # Decode
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print("\nGenerated output:", generated_text)
        
        # Check if output looks like SQL
        sql_keywords = ['select', 'from', 'where', 'join', 'group by', 'order by']
        looks_like_sql = any(keyword in generated_text.lower() for keyword in sql_keywords)
        
        if looks_like_sql:
            print("\n✅ Output contains SQL-like syntax!")
        else:
            print("\n❌ Output doesn't look like SQL. You need a model fine-tuned for SQL generation!")
            print("Recommendation: Use a model specifically trained for text-to-SQL, such as:")
            print("- PICARD")
            print("- CodeT5")
            print("- A fine-tuned version of T5 on SQL dataset")
            
    except Exception as e:
        print(f"\n❌ Error occurred during testing: {str(e)}")
        return False

if __name__ == "__main__":
    test_sql_generation()
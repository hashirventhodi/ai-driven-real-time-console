# nlp/hf_sql_model.py

import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer

class HFSQLModel:
    def __init__(self, model_name_or_path="t5-small", max_length=128):
        """
        :param model_name_or_path: a model identifier from Hugging Face Hub
                                   or path to a local checkpoint, e.g. 't5-small'
        :param max_length: maximum length of generated tokens
        """
        self.tokenizer = T5Tokenizer.from_pretrained(model_name_or_path)
        self.model = T5ForConditionalGeneration.from_pretrained(model_name_or_path)
        self.max_length = max_length

    def generate_sql(self, prompt: str) -> str:
        """
        Generate a SQL command from the given prompt. 
        The prompt should contain instructions like:
          - "Output ONLY the SQL query"
          - A summarized schema
          - The user query

        :param prompt: textual prompt for T5
        :return: the generated SQL query (string)
        """
        # Tokenize the prompt
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt")
        
        # Generate
        outputs = self.model.generate(
            input_ids=input_ids,
            max_length=self.max_length,
            num_beams=4,          # You can increase beams for better results
            early_stopping=True,  # Stop when an end token is produced
            no_repeat_ngram_size=2  # Helps reduce repetition
        )
        
        # Decode the output tokens back to text
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return generated_text

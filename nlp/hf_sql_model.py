# nlp/hf_sql_model.py
import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer

class HFSQLModel:
    def __init__(self, model_name_or_path="t5-small"):
        self.tokenizer = T5Tokenizer.from_pretrained(model_name_or_path)
        self.model = T5ForConditionalGeneration.from_pretrained(model_name_or_path)

    def generate_sql(self, prompt: str) -> str:
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt")
        outputs = self.model.generate(
            input_ids=input_ids,
            max_length=128,
            num_beams=4,
            early_stopping=True
        )
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

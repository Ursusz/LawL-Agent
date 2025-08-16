from transformers import AutoTokenizer, AutoModel
import torch

model_name = "readerbench/distilroberta-base-romanian"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

def get_text_embeddings(text):
    inputs = tokenizer(text, return_tensors='pt', padding=True, truncation=True)

    with torch.no_grad():
        ouputs = model(**inputs)

    embeddings = ouputs.last_hidden_state[:, 0, :]
    return embeddings
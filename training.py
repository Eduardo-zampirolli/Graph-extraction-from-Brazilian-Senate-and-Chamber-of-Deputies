from transformers import pipeline

# Load trained model
ner_pipeline = pipeline(
    "ner",
    model="./parliamentary_ner_model",
    tokenizer="./parliamentary_ner_model"
)

# Example prediction
results = ner_pipeline("O SR. RELATOR (Carlos Gomes) apresentou o parecer.")
print([(x['word'], x['entity']) for x in results if x['entity'] != 'O'])
import torch
from transformers import AutoModelForTokenClassification, AutoTokenizer
import os

# parameters
model_name = "pierreguillou/ner-bert-base-cased-pt-lenerbr"
model = AutoModelForTokenClassification.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# --- Input File Handling ---
input_path = "senado/2024/26007.txt"

try:
    with open(input_path, 'r', encoding='utf-8') as f:
        input_text = f.read()
except FileNotFoundError:
    print(f"Error: Could not read input file '{input_path}'. Exiting.")
    exit()
# -------------------------

# --- Corrected Tokenization ---
# You can uncomment the next line to verify if model_max_length is indeed very large
# print(f"DEBUG: tokenizer.model_max_length reports: {tokenizer.model_max_length}")

inputs = tokenizer(input_text,
                   # max_length=tokenizer.model_max_length, # <<< This likely caused the OverflowError
                   max_length=512,                      # <<< Use explicit standard BERT max length
                   truncation=True,
                   return_tensors="pt",
                   return_offsets_mapping=True)
# -----------------------------


# We need offset mapping for reconstruction, remove it before passing to model
offset_mapping = inputs.pop("offset_mapping")[0].tolist() # Convert to list for easier indexing
# Get tokens using tokenizer method (ensure it handles potential WordPiece/BPE prefixes like '##')
tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])


# Get predictions
with torch.no_grad():
    outputs = model(**inputs).logits
predictions = torch.argmax(outputs, dim=2)[0].tolist() # Convert to list


# --- Corrected Entity Extraction Logic ---
# (Keep the entity extraction logic from the previous correct answer)
entities = []
current_entity = None

for idx, prediction_id in enumerate(predictions):
    label = model.config.id2label[prediction_id]
    # Ensure offset_mapping has the expected length, handle potential mismatch if needed
    if idx >= len(offset_mapping):
        print(f"Warning: Index {idx} out of bounds for offset_mapping (length {len(offset_mapping)}). Skipping token.")
        continue
    start_offset, end_offset = offset_mapping[idx]

    # Ignore special tokens and padding which have (0, 0) offset mapping
    # Also check for None offsets just in case
    if start_offset is None or end_offset is None or (start_offset == 0 and end_offset == 0):
        continue

    is_beginning = label.startswith("B-")
    is_inside = label.startswith("I-")
    entity_type = label[2:] if (is_beginning or is_inside) else None

    # If the current token is the beginning of a new entity (B- tag)
    if is_beginning:
        # First, save the previous entity if it exists *and* if it's a PESSOA
        if current_entity and current_entity["entity"] == "PESSOA":
            entities.append(current_entity)

        # Start the new entity
        current_entity = {
            "entity": entity_type,
            "text": input_text[start_offset:end_offset],
            "start": start_offset,
            "end": end_offset
        }

    # If the current token continues an entity (I- tag)
    elif is_inside:
        if current_entity and current_entity["entity"] == entity_type:
            # Extend the current entity's end offset
            current_entity["end"] = end_offset
            # Update the text by re-slicing the original input text
            current_entity["text"] = input_text[current_entity["start"]:current_entity["end"]]
        else:
             # Save the previous entity if it was a PESSOA
            if current_entity and current_entity["entity"] == "PESSOA":
                entities.append(current_entity)
            current_entity = None # Discard the broken entity segment

    # If the current token is outside any entity (O tag)
    else: # label == "O"
         # Save the previous entity if it exists *and* if it's a PESSOA
        if current_entity and current_entity["entity"] == "PESSOA":
            entities.append(current_entity)
        current_entity = None # Reset tracker

# After the loop, check if the last tracked entity is a PESSOA and needs saving
if current_entity and current_entity["entity"] == "PESSOA":
    entities.append(current_entity)

# --- Print only PESSOA entities ---
print("\n--- Extracted PESSOA Entities ---")
if entities:
    for entity in entities:
        print(entity)
else:
    print("No PESSOA entities found.")
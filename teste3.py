import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification
import os
import json
import re
import numpy as np
from unicodedata import normalize
from collections import defaultdict

# Initialize device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using {device}")

# Load model and tokenizer
model_name = "pierreguillou/ner-bert-base-cased-pt-lenerbr"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForTokenClassification.from_pretrained(model_name).to(device)

class NumpyEncoder(json.JSONEncoder):
    """Custom encoder for numpy data types"""
    def default(self, obj):
        if isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        return super().default(obj)

def clean_text(text):
    """Normalize text and remove existing annotations"""
    text = normalize('NFC', text)
    # Remove all annotations of format [TAG:content]
    return re.sub(r'\[[A-Z]+:[^\]]*\]', '', text)

def tokenize_with_offsets(text):
    """Tokenize text while preserving character offsets"""
    encoding = tokenizer(text, return_offsets_mapping=True, return_tensors="pt")
    return (
        encoding["input_ids"].to(device),
        encoding["attention_mask"].to(device),
        encoding["offset_mapping"][0].cpu().numpy()
    )

def predict_entities(input_ids, attention_mask):
    """Predict entities using PyTorch model"""
    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
    predictions = torch.argmax(outputs.logits, dim=2)[0].cpu().numpy()
    scores = torch.max(torch.softmax(outputs.logits, dim=2), dim=2)[0][0].cpu().numpy()
    return predictions, scores

def process_long_text(text, original_text, window_size=400, stride=100):
    """Process long text with sliding window"""
    all_entities = []
    
    for i in range(0, len(text), window_size - stride):
        chunk_start = i
        chunk_end = min(i + window_size, len(text))
        chunk = text[chunk_start:chunk_end]
        
        try:
            input_ids, attention_mask, offsets = tokenize_with_offsets(chunk)
            predictions, scores = predict_entities(input_ids, attention_mask)
            entities = extract_entities(predictions, scores, offsets, chunk, original_text, chunk_start)
            all_entities.extend(entities)
        except Exception as e:
            print(f"Error processing chunk {chunk_start}-{chunk_end}: {str(e)[:100]}...")
    
    return all_entities

def extract_entities(predictions, scores, offsets, chunk, original_text, chunk_start):
    """Convert model predictions to entity spans"""
    current_entity = None
    entities = []
    
    for idx, (pred, score) in enumerate(zip(predictions, scores)):
        # Skip special tokens ([CLS], [SEP], etc.)
        if offsets[idx][0] == offsets[idx][1]:
            continue
            
        label = model.config.id2label[pred]
        
        if label.startswith("B-"):
            if current_entity:
                entities.append(current_entity)
            current_entity = {
                'start': int(offsets[idx][0] + chunk_start),
                'end': int(offsets[idx][1] + chunk_start),
                'score': float(score),
                'entity_group': label[2:],
                'word': original_text[int(offsets[idx][0] + chunk_start):int(offsets[idx][1] + chunk_start)]
            }
        elif label.startswith("I-") and current_entity:
            if label[2:] == current_entity['entity_group']:
                current_entity['end'] = int(offsets[idx][1] + chunk_start)
                current_entity['word'] = original_text[current_entity['start']:current_entity['end']]
                current_entity['score'] = min(current_entity['score'], float(score))
        else:
            if current_entity:
                entities.append(current_entity)
            current_entity = None
    
    if current_entity:
        entities.append(current_entity)
    
    return entities


def merge_and_filter_entities(entities):
    """Merge adjacent entities of the same type"""
    if not entities:
        return []
    
    # Sort by start position
    entities.sort(key=lambda x: x['start'])
    
    merged = [entities[0]]
    for current in entities[1:]:
        last = merged[-1]
        
        # Merge if adjacent and same entity type
        if (current['entity_group'] == last['entity_group'] and 
            current['start'] <= last['end']):
            # Extend the entity span
            merged[-1]['word'] = last['word'] + current['word'][(last['end']-current['start']):]
            merged[-1]['end'] = current['end']
            merged[-1]['score'] = min(last['score'], current['score'])
        else:
            merged.append(current)
    
    return merged

def create_annotations(original_text, entities):
    """Create final annotated text"""
    # Start with clean text (no existing annotations)
    clean_text_content = clean_text(original_text)
    annotated = clean_text_content
    
    # Process entities in reverse order of their start position
    for ent in sorted(entities, key=lambda x: -x['start']):
        if ent['entity_group'] == 'PESSOA':
            annotated = (
                annotated[:ent['start']] + 
                f"[PESSOA:{annotated[ent['start']:ent['end']]}]" + 
                annotated[ent['end']:]
            )
    
    return annotated

def process_text_file(input_path):
    """Process a text file end-to-end"""
    with open(input_path, 'r', encoding='utf-8') as f:
        original_text = f.read()
    
    clean_text_content = clean_text(original_text)
    entities = process_long_text(clean_text_content, original_text)
    merged_entities = merge_and_filter_entities(entities)
    
    # Convert all numbers to native Python types
    people_entities = []
    for ent in merged_entities:
        if ent['entity_group'] == 'PESSOA':
            people_entities.append({
                'name': str(ent['word']),
                'confidence': float(ent['score']),
                'start_pos': int(ent['start']),
                'end_pos': int(ent['end'])
            })
    
    annotated_text = create_annotations(original_text, merged_entities)
    return people_entities, annotated_text

def save_results(output_dir, base_name, people_list, annotated_text):
    """Save results to files with proper serialization"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Save entities with custom encoder
    with open(os.path.join(output_dir, f"{base_name}_entities.json"), 'w', encoding='utf-8') as f:
        json.dump(people_list, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
    
    # Save annotated text
    with open(os.path.join(output_dir, f"{base_name}_annotated.txt"), 'w', encoding='utf-8') as f:
        f.write(annotated_text)

if __name__ == "__main__":
    input_file = "senado/2024/26007.txt"  # Replace with your file path
    output_dir = "ner_results3"
    
    print(f"Processing file: {input_file}")
    people, annotated = process_text_file(input_file)
    
    base_name = os.path.basename(input_file).replace('.txt', '')
    save_results(output_dir, base_name, people, annotated)
    
    print(f"\nExtracted {len(people)} people:")
    for i, person in enumerate(people[:20], 1):
        print(f"{i}. {person['name']} (confidence: {person['confidence']:.4f})")
    
    print("\nSample annotated text:")
    print(annotated[:500] + "...")
    
    print(f"\nResults saved to: {output_dir}/")
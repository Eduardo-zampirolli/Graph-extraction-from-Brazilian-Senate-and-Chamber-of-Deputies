import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline
import os
import json
import re
from unicodedata import normalize

# Initialize with GPU if available
device = 0 if torch.cuda.is_available() else -1
print(f"Using {'GPU' if device == 0 else 'CPU'}")

# Load model with optimized settings
model_name = "pierreguillou/ner-bert-base-cased-pt-lenerbr"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForTokenClassification.from_pretrained(model_name)

def clean_text(text):
    """Normalize text and remove existing annotations"""
    text = normalize('NFC', text)
    return re.sub(r'<\/?[A-Z]+>', '', text)

def process_text_with_overlap(text, original_text, window_size=1000, stride=200):
    """Process long text with sliding window and proper position mapping"""
    nlp = pipeline(
        "ner",
        model=model,
        tokenizer=tokenizer,
        aggregation_strategy="simple",
        device=device,
        framework="pt"
    )
    
    all_entities = []
    
    for i in range(0, len(text), window_size - stride):
        chunk_start = i
        chunk_end = min(i + window_size, len(text))
        chunk = text[chunk_start:chunk_end]
        
        try:
            entities = nlp(chunk)
            # Adjust positions to original text
            for ent in entities:
                ent['start'] += chunk_start
                ent['end'] += chunk_start
                # Get actual text from original
                ent['word'] = original_text[ent['start']:ent['end']]
            all_entities.extend(entities)
        except Exception as e:
            print(f"Error processing chunk {i}-{i+window_size}: {str(e)[:100]}...")
    
    return all_entities

def merge_entities(entities):
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

def create_annotated_text(original_text, entities):
    """Create final annotated text without nested tags"""
    # Sort entities by start position (descending)
    sorted_entities = sorted(entities, key=lambda x: -x['start'])
    
    annotated = original_text
    for ent in sorted_entities:
        if ent['entity_group'] == 'PESSOA':
            # Insert annotation
            annotated = (
                annotated[:ent['start']] + 
                f"[PESSOA:{annotated[ent['start']:ent['end']]}]" + 
                annotated[ent['end']:]
            )
    
    # Clean any residual artifacts
    annotated = re.sub(r'\[PESSOA:\[PESSOA:(.*?)\]\]', r'[PESSOA:\1]', annotated)
    annotated = re.sub(r'\[PESSOA:\](.*?)\[PESSOA:\]', r'[PESSOA:\1]', annotated)
    
    return annotated

def process_text_file(input_path):
    """Process a text file end-to-end"""
    with open(input_path, 'r', encoding='utf-8') as f:
        original_text = f.read()
    
    clean_text_content = clean_text(original_text)
    
    # Process with sliding window
    entities = process_text_with_overlap(clean_text_content, original_text)
    
    # Merge adjacent entities
    merged_entities = merge_entities(entities)
    
    # Remove duplicates (same span)
    unique_entities = []
    seen_spans = set()
    for ent in merged_entities:
        span = (ent['start'], ent['end'])
        if span not in seen_spans:
            seen_spans.add(span)
            unique_entities.append(ent)
    
    # Filter only PESSOA entities
    people_entities = [
        {
            'name': ent['word'],
            'confidence': float(ent['score']),
            'start_pos': ent['start'],
            'end_pos': ent['end']
        }
        for ent in unique_entities if ent['entity_group'] == 'PESSOA'
    ]
    
    # Create clean annotated text
    annotated_text = create_annotated_text(original_text, unique_entities)
    
    return people_entities, annotated_text

def save_results(output_dir, base_name, people_list, annotated_text):
    """Save results to files"""
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, f"{base_name}_entities.json"), 'w', encoding='utf-8') as f:
        json.dump(people_list, f, ensure_ascii=False, indent=2)
    
    with open(os.path.join(output_dir, f"{base_name}_annotated.txt"), 'w', encoding='utf-8') as f:
        f.write(annotated_text)

def main():
    input_file = "senado/2024/26007.txt"  # Replace with your file path
    output_dir = "ner_results2"
    
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

if __name__ == "__main__":
    main()
from transformers import pipeline
import os
import json
import re
from unicodedata import normalize
from collections import defaultdict

# Initialize NER pipeline
nlp_ner = pipeline(
    "ner",
    model="pierreguillou/ner-bert-base-cased-pt-lenerbr",
    aggregation_strategy="simple",
    device=-1  # Use -1 for CPU, 0 for GPU
)

def clean_text(text):
    """Normalize text and remove any existing annotations"""
    text = normalize('NFC', text)
    return re.sub(r'<\/?[A-Z]+>', '', text)

def merge_wordpieces(entities, original_text):
    """Merge wordpieces and adjacent PESSOA entities"""
    merged = []
    i = 0
    n = len(entities)
    
    while i < n:
        current = entities[i]
        
        if current['entity_group'] == 'PESSOA':
            # Start with current word
            full_word = current['word']
            start = current['start']
            end = current['end']
            min_score = current['score']
            
            # Look ahead to merge
            j = i + 1
            while j < n:
                next_ent = entities[j]
                
                # Check if next is PESSOA and either:
                # 1. Directly adjacent in text, or
                # 2. Current word ends with ## and next starts with it (BERT wordpieces)
                if (next_ent['entity_group'] == 'PESSOA' and
                    (next_ent['start'] == end or 
                     (full_word.endswith('##') and next_ent['word'].startswith(full_word[2:])))):
                    
                    # Handle BERT wordpieces
                    if full_word.endswith('##'):
                        full_word = full_word[:-2] + next_ent['word']
                    else:
                        full_word += ' ' + next_ent['word']
                    
                    end = next_ent['end']
                    min_score = min(min_score, next_ent['score'])
                    j += 1
                else:
                    break
            
            # Get actual text from original
            actual_text = original_text[start:end]
            
            # Clean any ## artifacts
            clean_name = re.sub(r'##', '', actual_text)
            clean_name = re.sub(r'\s+', ' ', clean_name).strip()
            
            merged.append({
                'word': clean_name,
                'score': min_score,
                'start': start,
                'end': end,
                'entity_group': 'PESSOA'
            })
            i = j
        else:
            merged.append(current)
            i += 1
    
    return merged

def remove_duplicates(entities):
    """Remove duplicate entities that reference the same text span"""
    seen = defaultdict(list)
    unique = []
    
    for ent in entities:
        if ent['entity_group'] == 'PESSOA':
            key = (ent['start'], ent['end'])
            if key not in seen:
                seen[key] = ent
                unique.append(ent)
        else:
            unique.append(ent)
    
    return unique

def process_text_chunk(text_chunk, original_text):
    """Process a text chunk with enhanced merging"""
    try:
        entities = nlp_ner(text_chunk)
        merged = merge_wordpieces(entities, original_text)
        deduped = remove_duplicates(merged)
        return deduped
    except Exception as e:
        print(f"Error processing chunk: {str(e)[:100]}...")
        return []

def annotate_text(original_text, entities):
    """Add proper annotations around entities in text"""
    sorted_entities = sorted(entities, key=lambda x: -x['start'])
    annotated = original_text
    for entity in sorted_entities:
        if entity['entity_group'] == 'PESSOA':
            start = entity['start']
            end = entity['end']
            annotation = f"[PESSOA:{original_text[start:end]}]"
            annotated = annotated[:start] + annotation + annotated[end:]
    return annotated

def process_text_file(input_path):
    """Process a text file with enhanced entity handling"""
    with open(input_path, 'r', encoding='utf-8') as f:
        original_text = f.read()
    
    clean_text_content = clean_text(original_text)
    
    # Process in chunks of 1000 characters with overlap
    chunk_size = 1000
    overlap = 200
    chunks = []
    for i in range(0, len(clean_text_content), chunk_size - overlap):
        chunks.append((i, min(i + chunk_size, len(clean_text_content))))
    
    all_entities = []
    annotated_parts = []
    
    for start, end in chunks:
        chunk_text = clean_text_content[start:end]
        entities = process_text_chunk(chunk_text, original_text[start:end])
        
        # Adjust positions to original text
        adjusted_entities = []
        for ent in entities:
            adjusted_ent = ent.copy()
            adjusted_ent['start'] += start
            adjusted_ent['end'] += start
            adjusted_entities.append(adjusted_ent)
        
        all_entities.extend(adjusted_entities)
        annotated_parts.append(annotate_text(chunk_text, entities))
    
    # Final deduplication across chunks
    all_entities = remove_duplicates(all_entities)
    annotated_text = ''.join(annotated_parts)
    
    # Filter only PESSOA entities for the list
    people_entities = [
        {
            'name': e['word'],
            'confidence': float(e['score']),
            'start_pos': e['start'],
            'end_pos': e['end']
        } 
        for e in all_entities if e['entity_group'] == 'PESSOA'
    ]
    
    return people_entities, annotated_text

# ... (keep the save_results and main functions from previous example)

def save_results(output_dir, base_name, people_list, annotated_text):
    """Save results to files"""
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, f"{base_name}_entities.json"), 'w', encoding='utf-8') as f:
        json.dump(people_list, f, ensure_ascii=False, indent=2)
    
    with open(os.path.join(output_dir, f"{base_name}_annotated.txt"), 'w', encoding='utf-8') as f:
        f.write(annotated_text)

def main():
    input_file = "senado/2024/26007.txt"
    output_dir = "ner_results"
    
    print(f"Processing file: {input_file}")
    people, annotated = process_text_file(input_file)
    
    base_name = os.path.basename(input_file).replace('.txt', '')
    save_results(output_dir, base_name, people, annotated)
    
    print(f"\nExtracted {len(people)} people:")
    for i, person in enumerate(people[:20], 1):
        print(f"{i}. {person['name']} (confidence: {person['confidence']:.4f})")
    
    print(f"\nResults saved to: {output_dir}/")

if __name__ == "__main__":
    main()

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
parliamentary_presidente_regex = re.compile(
            r"(?:\bO\s+SR\.|\bA\s+SRA\.)\s+PRESIDENTE\s+\(([^.)]+)\.(?:[^/]+/)?([A-Z]+)\s*-\s*([A-Z]{2})\)",
            re.IGNORECASE
        )
        # Pattern 2: O SR./A SRA. TITLE. NAME (Bloco.../Party - State)
parliamentary_other_regex = re.compile(
            # Start with O SR. or A SRA.
            r"(?:\bO\s+SR\.|\bA\s+SRA\.)\s+"
            # Capture Title(s) and Name (all caps/dots/spaces)
            r"((?:[A-ZÀ-Ú]+\.?\s+)*[A-ZÀ-Ú]+)"
            # Match the parenthesis part
            r"\s+\((?:[^/]+/)?([A-Z]+)\s*-\s*([A-Z]{2})\)",
            re.IGNORECASE
        )
def rules(text):
    rule_entities = []
    processed_spans = set() # To avoid double processing

    # --- New Parliamentary Rules --- 
        
    # Match Pattern 1 (Presidente)
    for match in parliamentary_presidente_regex.finditer(text):
        start, end = match.span()
        # Check for overlap with already processed spans
        if any(max(start, ps) < min(end, pe) for ps, pe in processed_spans):
            continue
                
        name_part = match.group(1).strip()
        party = match.group(2).strip()
        state = match.group(3).strip()
        # Construct the desired entity string
        entity_word = f"Presidente {name_part} {party}"
            
        rule_entities.append({
            "entity_group": "PESSOA",
            "score": 1.0, 
            "word": entity_word,
            "start": start, # Use the full match span
            "end": end,
            "source": "rule_parliamentary_presidente",
            "metadata": {  # Add metadata field
                "party": party,
                "state": state,
                "title": "PRESIDENTE"
            }
        })
        processed_spans.add((start, end))

    # Match Pattern 2 (Other Title/Name)
    for match in parliamentary_other_regex.finditer(text):
        start, end = match.span()
        # Check for overlap with already processed spans
        if any(max(start, ps) < min(end, pe) for ps, pe in processed_spans):
            continue

        title_name_part = match.group(1).strip()
        party = match.group(2).strip()
        state = match.group(3).strip()
        # Construct the desired entity string
        entity_word = f"{title_name_part} {party}"
            
        rule_entities.append({
            "entity_group": "PESSOA",
            "score": 1.0, 
            "word": entity_word,
            "start": start, # Use the full match span
            "end": end,
            "source": "rule_parliamentary_presidente",
            "metadata": {  # Add metadata field
                "party": party,
                "state": state,
                "title": title_name_part
            }
        })
        processed_spans.add((start, end))
    return rule_entities

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
        """Improved merging of adjacent entities with better handling of all-caps names"""
        if not entities:
            return []
        
        # Sort by start position
        entities.sort(key=lambda x: x["start"])
        
        merged = []
        for entity in entities:
            if not merged:
                merged.append(entity)
                continue
                
            last = merged[-1]
            
            # Check if we should merge with previous entity
            should_merge = (
                entity["entity_group"] == last["entity_group"] and  # Same entity type
                entity["start"] <= last["end"] + 1 and  # Adjacent or overlapping
                # Additional check for all-caps names
                (entity["word"].isupper() or last["word"].isupper() or 
                entity["start"] <= last["end"])
            )
            
            if should_merge:
                # Calculate overlap
                overlap = last["end"] - entity["start"]
                if overlap >= 0:
                    # Overlapping - append non-overlapping part
                    merged[-1]["word"] += entity["word"][overlap:]
                else:
                    # Adjacent - add space between
                    merged[-1]["word"] += " " + entity["word"]
                
                # Update end position
                if merged[-1]["end"] < entity["end"]:
                    merged[-1]["end"] = entity["end"]
                
                # Keep minimum score
                merged[-1]["score"] = min(last["score"], entity["score"])
            else:
                merged.append(entity)
        joined = []
        for ent in merged:
            if not joined:
                joined.append(ent)
                continue
            last = joined[-1]
            should_join = (
                ent["entity_group"] == last["entity_group"] and
                ent["start"] - last["end"] == 1
            )
            if should_join:
                joined[-1]["word"] += " " + ent["word"]
                joined[-1]["end"] = ent["end"]
                joined[-1]["score"] = min(last["score"], ent["score"])
            else:
                joined.append(ent)
        return joined
#def group_entities()
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
    rule = rules(original_text)
    # Process with sliding window
    general = process_text_with_overlap(clean_text_content, original_text)
    general.extend(rule)
    entities = []
    for ent in general:
        if ent['entity_group'] == 'PESSOA':
            entities.append(ent)
            
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
    input_file ="/home/fz/Downloads/est_dir/senado_r/2021/10484.txt" # Replace with your file path
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
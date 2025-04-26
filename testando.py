from transformers import pipeline
import os
import json
import numpy as np

def split_text(text, chunk_size=400):
    """Simple text splitter that respects sentence boundaries"""
    chunks = []
    current_chunk = ""
    
    for sentence in text.replace('\n', ' ').split('. '):  # Split by sentences
        if len(current_chunk) + len(sentence) < chunk_size:
            current_chunk += sentence + ". "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def initialize_ner_pipeline():
    """Initialize the NER pipeline with proper settings"""
    return pipeline(
        "ner",
        model="pierreguillou/ner-bert-base-cased-pt-lenerbr",
        aggregation_strategy="simple",
        device=-1  # Force CPU (change to 0 for GPU)
    )

def extract_people(text_chunk, nlp_ner):
    """Extract people from a single text chunk"""
    try:
        ner_results = nlp_ner(text_chunk)
        return [entity for entity in ner_results if entity["entity_group"] == "PESSOA"]
    except Exception as e:
        print(f"Error processing chunk: {str(e)[:100]}...")
        return []

class NumpyEncoder(json.JSONEncoder):
    """Custom encoder for numpy data types"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

def process_text_file(input_path, output_dir):
    """Process a text file and save results"""
    nlp_ner = initialize_ner_pipeline()
    
    with open(input_path, "r", encoding="utf-8") as file:
        text = file.read()
    
    chunks = split_text(text)
    all_people = []
    
    for chunk in chunks:
        all_people.extend(extract_people(chunk, nlp_ner))
    
    # Prepare output with proper type conversion
    results = [{
        "name": p["word"],
        "confidence": float(p["score"])  # Explicit conversion to Python float
    } for p in all_people]
    
    # Save results
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 
                             os.path.basename(input_path).replace(".txt", "_people.json"))
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
    
    return results

if __name__ == "__main__":
    input_file = "senado/2024/26007.txt"  # Change to your file path
    output_dir = "ner_results"
    
    print(f"Processing file: {input_file}")
    people = process_text_file(input_file, output_dir)
    
    print(f"\nFound {len(people)} people:")
    for i, person in enumerate(people[:20], 1):  # Print first 20
        print(f"{i}. {person['name']} (confidence: {person['confidence']:.4f})")
    
    print(f"\nFull results saved to: {output_dir}")
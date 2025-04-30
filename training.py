#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
import torch
import sys
import numpy as np
import json
import math
import os
import glob
import time
import re # Import regex module

class NERPersonExtractorWithMerging:
    """
    Extracts Person entities (PESSOA) using a combination of:
    1. Rule-based detection for names following "O SR." and "A SRA."
    2. Hugging Face pipeline (pierreguillou/ner-bert-base-cased-pt-lenerbr)
    Includes post-processing logic to merge split entities and normalize name capitalization.
    """
    def __init__(self, model_name="pierreguillou/ner-bert-base-cased-pt-lenerbr"):
        self.model_name = model_name
        print(f"Loading model: {self.model_name}...")
        start_time = time.time()
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForTokenClassification.from_pretrained(model_name)
        self.device = 0 if torch.cuda.is_available() else -1
        # Corrected f-string syntax using single quotes inside
        print(f"Device set to use: {'GPU' if self.device == 0 else 'CPU'}") # Corrected line
        
        self.max_seq_len = self.tokenizer.model_max_length
        if not isinstance(self.max_seq_len, int) or self.max_seq_len > 512:
            print(f"Warning: tokenizer.model_max_length is {self.max_seq_len}. Setting to 512.")
            self.max_seq_len = 512
        print(f"Using max sequence length: {self.max_seq_len}")

        self.ner_pipeline = pipeline(
            "ner", 
            model=self.model, 
            tokenizer=self.tokenizer, 
            aggregation_strategy="simple",
            device=self.device,
            framework="pt"
        )
        end_time = time.time()
        print(f"Model loaded in {end_time - start_time:.2f} seconds.")
        
        # Regex for titles (case-insensitive for SR/SRA, requires dot)
        # Captures the name part, handling potential parenthesized info
        # Name part: At least one capitalized word, followed by zero or more words 
        # (including connectors like 'de', 'da') until a likely boundary.
        # Boundary: newline, double space, period followed by space, or end of string.
        # We capture up to the first boundary like '.) -' or newline
        self.title_regex = re.compile(
            r"(?:\bO\s+SR\.|\bA\s+SRA\.)\s+" # Match title O SR. or A SRA.
            r"((?:[A-ZÀ-Ú][a-zà-ú]+(?:\s+(?:de|da|do|dos|das|e)\s+)?)+[A-ZÀ-Ú][a-zà-ú\s]*)" # Capture Name part
            # Optional: Handle trailing info like (Party - State) or titles
            # r"(?:\s*\([^)]+\))?" # Optional parenthesized info
            , re.IGNORECASE
        )

    def _extract_persons_rule_based(self, text):
        """Extracts persons based on O SR./A SRA. title rule."""
        rule_entities = []
        for match in self.title_regex.finditer(text):
            name = match.group(1).strip()
            # Further refine name extraction if needed, e.g., remove trailing titles if captured
            # Example: If regex captured "Nome Sobrenome. Bloco...", trim after period.
            if "." in name:
                 # Find the first period that likely terminates the name, not initials like J. R. R.
                 period_match = re.search(r"\.\s+(?:[A-ZÀ-Ú(]|\n|$)", name) # Period followed by space and uppercase/paren/newline/end
                 if period_match:
                     name = name[:period_match.start()].strip()
                 # else: keep name as is if period seems internal (e.g., initials)
                 
            # Remove potential trailing parenthesized info if captured by mistake
            name = re.sub(r"\s*\([^)]*\)$", "", name).strip()
            
            # Basic validation: Check if name seems plausible (e.g., not empty)
            if name and len(name) > 1:
                rule_entities.append({
                    "entity_group": "PESSOA",
                    "score": 1.0,  # Assign high confidence score for rule-based matches
                    "word": name, # Normalization happens later
                    "start": match.start(1),
                    "end": match.start(1) + len(name),
                    "source": "rule"
                })
        return rule_entities

    def extract_persons(self, text):
        """Extracts and merges person entities using rules and model."""
        try:
            # 1. Extract using Rules
            rule_entities = self._extract_persons_rule_based(text)

            # 2. Extract using Model with safer chunking
            model_entities = []
            
            # Calculate approximate chunk size in characters (conservative estimate)
            # Assuming ~4 chars per token, with 25% buffer for tokenization variance
            chunk_char_size = 400 
            overlap_size = 100  # Character overlap between chunks
            
            # Process in chunks if text is long
            if len(text) > chunk_char_size:
                for i in range(0, len(text), chunk_char_size - overlap_size):
                    chunk_start = max(0, i)
                    chunk_end = min(i + chunk_char_size, len(text))
                    chunk_text = text[chunk_start:chunk_end]
                    
                    try:
                        chunk_entities = self.ner_pipeline(chunk_text)
                        # Adjust offsets to original text positions
                        for entity in chunk_entities:
                            if entity.get("entity_group") == "PESSOA":
                                entity["start"] += chunk_start
                                entity["end"] += chunk_start
                                entity["word"] = text[entity["start"]:entity["end"]]
                                entity["source"] = "model"
                                model_entities.append(entity)
                    except Exception as e:
                        print(f"Error processing chunk: {e}")
                        continue
            else:
                # Process whole text if short enough
                chunk_entities = self.ner_pipeline(text)
                for entity in chunk_entities:
                    if entity.get("entity_group") == "PESSOA":
                        entity["source"] = "model"
                        model_entities.append(entity)

            # 3. Integrate Rule and Model Entities
            combined_entities = []
            covered_spans = []  # Store (start, end) of rule entities

            # Add all high-confidence rule entities first
            for rentity in rule_entities:
                combined_entities.append(rentity)
                covered_spans.append((rentity["start"], rentity["end"]))
            
            # Add model entities if they don't significantly overlap with rule entities
            for mentity in model_entities:
                is_covered = False
                for r_start, r_end in covered_spans:
                    # Check for significant overlap
                    overlap_start = max(mentity["start"], r_start)
                    overlap_end = min(mentity["end"], r_end)
                    overlap_len = max(0, overlap_end - overlap_start)
                    mentity_len = mentity["end"] - mentity["start"]
                    if overlap_len > 0.5 * mentity_len or (mentity["start"] >= r_start and mentity["end"] <= r_end):
                        is_covered = True
                        break
                if not is_covered:
                    combined_entities.append(mentity)

            # 4. Merge the combined list
            merged_persons = self._merge_split_persons(combined_entities, text)
            return merged_persons
            
        except Exception as e:
            print(f"Error during NER processing: {e}")
            import traceback
            traceback.print_exc()
            return []

    # --- Merging Logic (from previous version, slightly adapted) --- 
    def _should_merge(self, entity1, entity2, original_text):
        """Determine if two PESSOA entities should be merged, handling fragments."""
        MAX_DISTANCE = 5
        distance = entity2["start"] - entity1["end"]
        if distance < 0 or distance > MAX_DISTANCE: return False
        if distance == 0: return True
        text_between = original_text[entity1["end"]:entity2["start"]]
        if text_between.isspace(): return True
        if distance <= 1 and text_between.strip() in ("-", "'"): return True
        allowed_connectors = {"de", "da", "do", "dos", "das", "e"}
        words_between = text_between.strip().lower().split()
        if distance <= 3 and words_between and all(word in allowed_connectors for word in words_between): return True
        if len(entity1["word"]) == 1 and distance <= 1:
            if not words_between or all(word in allowed_connectors for word in words_between) or len(entity2["word"]) <= 2: return True
        if len(entity1["word"]) <= 2 and len(entity2["word"]) <= 2 and distance <= 1:
             if not words_between or all(word in allowed_connectors for word in words_between): return True
        return False

    def _merge_split_persons(self, person_entities, original_text):
        """Improved merging logic that handles partial name fragments."""
        if not person_entities:
            return []

        # Sort by start position, then by length (longer first)
        sorted_entities = sorted(person_entities, key=lambda x: (x["start"], -x["end"]))
        merged = []
        
        i = 0
        while i < len(sorted_entities):
            current = sorted_entities[i]
            current_text = original_text[current["start"]:current["end"]]
            
            # Initialize best candidate with current entity
            best_start = current["start"]
            best_end = current["end"]
            best_score = current["score"]
            best_text = current_text
            
            # Look ahead to find possible extensions
            j = i + 1
            while j < len(sorted_entities):
                next_entity = sorted_entities[j]
                
                # Stop if next entity doesn't overlap or is too far
                if next_entity["start"] > best_end + 3:  # Small gap allowed
                    break
                    
                # Calculate potential merged text
                potential_end = max(best_end, next_entity["end"])
                potential_text = original_text[best_start:potential_end]
                
                # Check if this produces a more complete name
                if (potential_end - best_start) <= 50:  # Reasonable name length limit
                    best_end = potential_end
                    best_score = max(best_score, next_entity["score"])
                    best_text = potential_text
                    j += 1
                else:
                    break
            
            # Create merged entity
            normalized_text = self._normalize_name_case(best_text)
            if self._is_valid_name(normalized_text):
                merged.append({
                    "entity_group": "PESSOA",
                    "score": best_score,
                    "word": normalized_text,
                    "start": best_start,
                    "end": best_end
                })
            
            i = j  # Skip ahead to next unmerged entity
        
        return merged

    def _is_valid_name(self, name):
        """Check if the name meets basic validity criteria."""
        name = name.strip()
        if not name or len(name) < 2:
            return False
        
        # Should contain at least some alphabetic characters
        if not any(c.isalpha() for c in name):
            return False
            
        return True
    
    def _normalize_name_case(self, name):
        if not name: return name
        name = name.strip()
        if not name: return name
        parts = []
        for part in name.split():
            lower_part = part.lower()
            if lower_part in {"de", "da", "do", "dos", "das", "e"}:
                parts.append(lower_part)
            else:
                # Capitalize first letter, lowercase rest, handle hyphens
                sub_parts = part.split('-')
                capitalized_sub_parts = []
                for sp in sub_parts:
                     if len(sp) > 1:
                         capitalized_sub_parts.append(sp[0].upper() + sp[1:].lower())
                     elif len(sp) == 1:
                         capitalized_sub_parts.append(sp.upper())
                     # else: empty string if double hyphen, ignore
                parts.append('-'.join(capitalized_sub_parts))
        return ' '.join(parts)

# --- Annotation and File Processing (Mostly unchanged) --- 
def annotate_text(text, entities):
    annotated_text = ""
    sorted_entities = sorted(entities, key=lambda x: x["start"])
    current_pos = 0
    for entity in sorted_entities:
        start = entity["start"]
        end = entity["end"]
        if start < current_pos: continue
        annotated_text += text[current_pos:start]
        annotated_text += f"[PESSOA:{entity['word']}]"
        current_pos = end
    annotated_text += text[current_pos:]
    return annotated_text

def convert_numpy_types(obj):
    if isinstance(obj, np.integer): return int(obj)
    elif isinstance(obj, np.floating): return float(obj)
    elif isinstance(obj, np.ndarray): return obj.tolist()
    elif isinstance(obj, dict): return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)): return [convert_numpy_types(item) for item in obj]
    return obj

def process_file(extractor, input_file_path, base_input_dir, base_output_dir):
    print(f"Processing file: {input_file_path}")
    start_time = time.time()
    relative_path = os.path.relpath(input_file_path, start=base_input_dir) 
    name_root = os.path.splitext(relative_path)[0]
    annotated_output_path = os.path.join(base_output_dir, name_root + ".annotated.txt")
    json_output_path = os.path.join(base_output_dir, name_root + ".entities.json")
    os.makedirs(os.path.dirname(annotated_output_path), exist_ok=True)
    try:
        with open(input_file_path, "r", encoding="utf-8") as f: text = f.read()
    except Exception as e: print(f"Error reading input file: {e}"); return
    entities = extractor.extract_persons(text)
    try:
        serializable_entities = convert_numpy_types(entities)
        with open(json_output_path, "w", encoding="utf-8") as f: json.dump(serializable_entities, f, ensure_ascii=False, indent=4)
    except Exception as e: print(f"Error writing JSON: {e}")
    annotated = annotate_text(text, entities)
    try:
        with open(annotated_output_path, "w", encoding="utf-8") as f: f.write(annotated)
    except Exception as e: print(f"Error writing annotated text: {e}")
    end_time = time.time()
    print(f"Finished processing {os.path.basename(input_file_path)} in {end_time - start_time:.2f} seconds. Outputs saved relative to {base_output_dir}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python training_v3.py <input_directory_or_file_path>") # Updated usage
        sys.exit(1)
    input_path = sys.argv[1]
    if os.path.isdir(input_path):
        base_input_dir = os.path.abspath(input_path)
        base_output_dir = os.path.join(os.path.dirname(base_input_dir), os.path.basename(base_input_dir) + "_output")
        print(f"Output directory: {base_output_dir}")
        os.makedirs(base_output_dir, exist_ok=True)
        glob_pattern = os.path.join(base_input_dir, "**", "*.txt")
        file_paths = [fp for fp in glob.glob(glob_pattern, recursive=True) if not (fp.endswith(".annotated.txt") or fp.endswith(".entities.json"))]
        print(f"Found {len(file_paths)} files to process recursively in {base_input_dir}")
    elif os.path.isfile(input_path) and input_path.endswith(".txt"):
        file_paths = [os.path.abspath(input_path)]
        base_input_dir = os.path.dirname(file_paths[0])
        base_output_dir = base_input_dir
        print(f"Processing single file: {file_paths[0]}")
        print(f"Output directory set to: {base_output_dir}")
    else:
        print(f"Error: Input path {input_path} is not a valid directory or .txt file.")
        sys.exit(1)
    if not file_paths: print("No .txt files found to process."); sys.exit(0)
    
    # Ensure required libraries are installed (redundant if already done, but safe)
    try:
        import transformers
        import torch
    except ImportError:
        print("Error: Required libraries (transformers, torch) not found. Please install them.")
        sys.exit(1)
        
    extractor = NERPersonExtractorWithMerging()
    total_start = time.time()
    for i, file_path in enumerate(file_paths):
        print(f"\n--- Processing file {i+1}/{len(file_paths)} --- ")
        process_file(extractor, file_path, base_input_dir, base_output_dir)
    total_time = time.time() - total_start
    print(f"\n\nFinished processing {len(file_paths)} files in {total_time:.2f} seconds.")
    avg_time = total_time / len(file_paths) if file_paths else 0
    print(f"Average time per file: {avg_time:.2f} seconds.")

if __name__ == "__main__":
    main()
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import os
import sys
import glob
import json
import re
import math
import time
from fuzzywuzzy import fuzz
from unicodedata import normalize

class IntegratedNERProcessor:
    """
    Performs Named Entity Recognition (NER) using a transformer model, 
    merges adjacent entities, removes duplicates, groups similar Person names, 
    and generates annotated text output.
    Combines extraction logic from teste_spacy.py with grouping from simple_ner_grouper.py.
    """
    def __init__(self, model_name="pierreguillou/ner-bert-base-cased-pt-lenerbr"):
        self.model_name = model_name
        print(f"Loading model: {self.model_name}...")
        start_time = time.time()

        self.device = 0 if torch.cuda.is_available() else -1
        device_str = "GPU" if self.device == 0 else "CPU"
        print(f"Device set to use: {device_str}")

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=False)
            self.model = AutoModelForTokenClassification.from_pretrained(model_name, local_files_only=False)
        except Exception as e:
            print(f"Error loading model {model_name}: {e}")
            print("Please ensure the model name is correct and you have an internet connection if it needs downloading.")
            sys.exit(1)

        # Handle potential issues with tokenizer.model_max_length
        self.max_seq_len = 512 # Default
        try:
            model_max_len = self.tokenizer.model_max_length
            # Added check for ridiculously large values sometimes returned
            if isinstance(model_max_len, int) and 0 < model_max_len <= 4096: # Set a reasonable upper limit
                self.max_seq_len = model_max_len
            else:
                 print(f"Warning: tokenizer.model_max_length ({model_max_len}) is invalid or too large. Setting to {self.max_seq_len}.")
        except Exception as e:
             print(f"Warning: Could not interpret tokenizer.model_max_length. Setting to {self.max_seq_len}. Error: {e}")
        print(f"Using max sequence length: {self.max_seq_len}")

        try:
            # Use aggregation_strategy="simple" as in source files
            self.ner_pipeline = pipeline(
                "ner", 
                model=self.model, 
                tokenizer=self.tokenizer, 
                aggregation_strategy="simple", 
                device=self.device,
                framework="pt"
            )
        except Exception as e:
            print(f"Error creating NER pipeline: {e}")
            sys.exit(1)
            
        end_time = time.time()
        print(f"Model loaded in {end_time - start_time:.2f} seconds.")
        self.parliamentary_presidente_regex = re.compile(
            r"(?:\bO\s+SR\.|\bA\s+SRA\.)\s+PRESIDENTE\s+\(([^.)]+)\.(?:[^/]+/)?([A-Z]+)\s*-\s*([A-Z]{2})\)",
            re.IGNORECASE
        )
        # Pattern 2: O SR./A SRA. TITLE. NAME (Bloco.../Party - State)
        self.parliamentary_other_regex = re.compile(
            # Start with O SR. or A SRA.
            r"(?:\bO\s+SR\.|\bA\s+SRA\.)\s+"
            # Capture Title(s) and Name (all caps/dots/spaces)
            r"((?:[A-ZÀ-Ú]+\.?\s+)*[A-ZÀ-Ú]+)"
            # Match the parenthesis part
            r"\s+\((?:[^/]+/)?([A-Z]+)\s*-\s*([A-Z]{2})\)",
            re.IGNORECASE
        )

    def _rule_based_ner(self, text, original_text):
        rule_entities = []
        processed_spans = set() # To avoid double processing

        # --- New Parliamentary Rules --- 
        
        # Match Pattern 1 (Presidente)
        for match in self.parliamentary_presidente_regex.finditer(text):
            start, end = match.span()
            # Check for overlap with already processed spans
            if any(max(start, ps) < min(end, pe) for ps, pe in processed_spans):
                continue
                
            name_part = match.group(1).strip()
            party = match.group(2).strip()
            state = match.group(3).strip()
            # Construct the desired entity string
            entity_word = f"Presidente {name_part} {party}-{state}"
            
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
        for match in self.parliamentary_other_regex.finditer(text):
            start, end = match.span()
            # Check for overlap with already processed spans
            if any(max(start, ps) < min(end, pe) for ps, pe in processed_spans):
                continue

            title_name_part = match.group(1).strip()
            party = match.group(2).strip()
            state = match.group(3).strip()
            # Construct the desired entity string
            entity_word = f"{title_name_part} {party}-{state}"
            
            rule_entities.append({
                "entity_group": "PESSOA",
                "score": 1.0, 
                "word": entity_word,
                "start": start, # Use the full match span
                "end": end,
                "source": "rule_parliamentary_other",
                "metadata": {  # Add metadata field
                    "party": party,
                    "state": state,
                    "title": title_name_part
                }
            })
            processed_spans.add((start, end))
        return rule_entities
   
    def _extract_entities_with_overlap(self, text, original_text, window_size=1000, stride=200):
        """Internal: Extract entities using sliding window. Based on teste_spacy.py."""
        all_entities = []
        text_len = len(text)
        if text_len == 0: return []
        
        # Ensure window_size and stride are reasonable relative to max_seq_len if needed
        # For now, using defaults from teste_spacy.py
        effective_window_size = min(window_size, text_len)
        effective_stride = min(stride, effective_window_size -1) if effective_window_size > 1 else 0
        if effective_stride < 0: effective_stride = 0

        num_chunks = math.ceil(max(1, text_len - effective_stride) / (effective_window_size - effective_stride))
        print(f"Processing text ({text_len} chars) in {num_chunks} chunks (window={effective_window_size}, stride={effective_stride})...")

        for i in range(num_chunks):
            chunk_start = i * (effective_window_size - effective_stride)
            chunk_end = min(chunk_start + effective_window_size, text_len)
            chunk_start = max(0, chunk_start) # Ensure start is not negative
            if chunk_start >= chunk_end: continue # Skip empty or invalid chunks

            chunk_text = text[chunk_start:chunk_end]
            
            try:
                # Disable gradient calculations for inference
                with torch.no_grad():
                    chunk_entities_raw = self.ner_pipeline(chunk_text)
                
                # Adjust positions to original text
                for ent in chunk_entities_raw:
                    if isinstance(ent.get("start"), int) and isinstance(ent.get("end"), int):
                        orig_start = ent["start"] + chunk_start
                        orig_end = ent["end"] + chunk_start
                        
                        # Boundary check against original text length
                        if 0 <= orig_start < orig_end <= len(original_text):
                            ent["start"] = orig_start
                            ent["end"] = orig_end
                            # Get actual text from original_text
                            ent["word"] = original_text[orig_start:orig_end]
                            all_entities.append(ent)
                        # else:
                            # print(f"Warning: Adjusted indices [{orig_start}:{orig_end}] out of bounds for entity in chunk {i}. Skipping.")
            except Exception as e:
                print(f"Error processing chunk {i} ({chunk_start}:{chunk_end}): {e}")
                continue
        
        return all_entities

    def _merge_adjacent_entities(self, entities):
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
        

    def _remove_duplicate_spans(self, entities):
        """Internal: Remove entities with identical start/end spans. Based on teste_spacy.py."""
        unique_entities = []
        seen_spans = set()
        # Sort by score descending to keep the highest-scoring duplicate
        entities.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        for ent in entities:
            span = (ent["start"], ent["end"])
            if span not in seen_spans:
                seen_spans.add(span)
                unique_entities.append(ent)
        # Re-sort by start position for consistency
        unique_entities.sort(key=lambda x: x["start"])
        return unique_entities

    def _normalize_for_comparison(self, name):
        """Internal: Simple normalization for grouping comparison. From simple_ner_grouper.py."""
        if not isinstance(name, str): return ""
        name = name.lower().strip()
        name = re.sub(r"[.,;:!?()\"\\]", "", name)
        name = " ".join(name.split())
        return name

    def _is_similar(self, name1, name2, threshold=85):
        """Internal: Check similarity using fuzzywuzzy. From simple_ner_grouper.py."""
        norm1 = self._normalize_for_comparison(name1)
        norm2 = self._normalize_for_comparison(name2)
        if not norm1 or not norm2: return False
        similarity = fuzz.token_set_ratio(norm1, norm2)
        return similarity >= threshold

    def _group_similar_persons(self, entities):
        """Internal: Group similar person entities. From simple_ner_grouper.py."""
        if not entities: return {}

        sorted_entities = sorted(entities, key=lambda x: (-len(x.get("word", "")), x.get("word", "")))
        
        grouped = {} 
        name_map = {}  
        
        for entity in sorted_entities:
            raw_word = entity.get("word")
            if not raw_word: continue 
            
            pos_info = (entity["start"], entity["end"], round(entity.get("score", 0.0), 4))
            
            if raw_word in name_map:
                canonical = name_map[raw_word]
                if canonical in grouped and pos_info not in grouped[canonical]:
                    grouped[canonical].append(pos_info)
                continue 
                
            found_match = False
            for canonical in list(grouped.keys()): 
                if self._is_similar(raw_word, canonical):
                    chosen_canonical = raw_word if len(raw_word) >= len(canonical) else canonical
                    
                    if chosen_canonical != canonical:
                        existing_positions = grouped.pop(canonical, []) 
                        if chosen_canonical not in grouped:
                            grouped[chosen_canonical] = []
                        for p in existing_positions:
                            if p not in grouped[chosen_canonical]:
                                grouped[chosen_canonical].append(p)
                        
                        for k, v in list(name_map.items()): 
                            if v == canonical:
                                name_map[k] = chosen_canonical
                        name_map[canonical] = chosen_canonical 
                    
                    if chosen_canonical not in grouped:
                         grouped[chosen_canonical] = []
                    if pos_info not in grouped[chosen_canonical]:
                        grouped[chosen_canonical].append(pos_info)
                        
                    name_map[raw_word] = chosen_canonical
                    found_match = True
                    break 
                    
            if not found_match:
                grouped[raw_word] = [pos_info]
                name_map[raw_word] = raw_word 
        
        final_grouped = {}
        for canonical, positions in grouped.items():
            unique_positions = sorted(list(set(positions)), key=lambda x: x[0])
            if unique_positions:
                 final_grouped[canonical] = unique_positions
        
        return final_grouped
    def _clean_text(self,text):
        """Normalize text and remove existing annotations"""
        text = normalize('NFC', text)
        return re.sub(r'<\/?[A-Z]+>', '', text)
    def process_text(self, text):
        """Public method: Extracts, merges, deduplicates, filters, and groups Person entities.
           Returns the grouped dictionary AND the list of unique PESSOA entities for annotation.
        """
        if not isinstance(text, str) or not text.strip():
            print("Warning: Input text is empty or not a string. Returning empty results.")
            return {}, []
            
        # 1. Extract raw entities using sliding window
        # Note: teste_spacy.py had a clean_text step, omitting here for simplicity unless needed
        clean_text_content = self._clean_text(text)
        raw_entities = self._extract_entities_with_overlap(clean_text_content, text) # Use text as original_text for now
        if not raw_entities:
            print("No entities found by the model.")
            return {}, []
            
        # 2. Merge adjacent entities of the same type
        merged_entities = self._merge_adjacent_entities(raw_entities)
        
        # 3. Remove duplicate spans (keeping highest score)
        unique_span_entities = self._remove_duplicate_spans(merged_entities)
        
        # 4. Filter for PESSOA entities
        pessoa_entities = [ent for ent in unique_span_entities if ent.get("entity_group") == "PESSOA"]
        if not pessoa_entities:
            print("No PESSOA entities found after merging and deduplication.")
            return {}, []
            
        # 5. Group similar PESSOA entities
        grouped_results = self._group_similar_persons(pessoa_entities)
        name_mapping = {}
        for canonical, positions in grouped_results.items():
            for start, end, score in positions:
                original_text = text[start:end]
                name_mapping[(start, end)] = canonical
        # Return grouped results and the unique PESSOA entities for annotation
        return grouped_results, pessoa_entities,name_mapping

# --- Standalone Functions --- 

def create_annotated_text(original_text, entities, name_mapping=None):
    """Create final annotated text using canonical names from grouping when available."""
    if not entities:
        return original_text
        
    pessoa_entities = [e for e in entities if e.get("entity_group") == "PESSOA" \
                      and isinstance(e.get("start"), int) and isinstance(e.get("end"), int)]
    if not pessoa_entities:
        return original_text
        
    sorted_entities = sorted(pessoa_entities, key=lambda x: -x["start"])
    
    annotated = original_text
    last_start = len(original_text)
    
    for ent in sorted_entities:
        start, end = ent["start"], ent["end"]
        if start >= end or end > last_start:
            continue
            
        # Use canonical name if available in name_mapping, otherwise use original text
        if name_mapping and (start, end) in name_mapping:
            entity_word = name_mapping[(start, end)]
        else:
            entity_word = annotated[start:end]
            
        annotated = (
            annotated[:start] 
            + f"<PESSOA:{entity_word}>" 
            + annotated[end:]
        )
        last_start = start

    return annotated

def save_grouped_entities(grouped_data, output_path):
    """Saves the grouped entity dictionary to a JSON file."""
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f: 
            serializable_data = json.loads(json.dumps(grouped_data, default=str)) 
            json.dump(serializable_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error writing JSON file {output_path}: {e}")

def save_annotated_text(annotated_text, output_path):
    """Saves the annotated text to a file."""
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(annotated_text)
    except Exception as e:
        print(f"Error writing annotated text file {output_path}: {e}")

def main():
    """Main function to handle command-line arguments and process files."""
    if len(sys.argv) != 2:
        print(f"Usage: python {os.path.basename(__file__)} <input_directory_or_file_path>")
        sys.exit(1)
        
    input_path = sys.argv[1]
    file_paths = []
    base_input_dir = ""
    base_output_dir = ""

    if os.path.isdir(input_path):
        base_input_dir = os.path.abspath(input_path)
        base_output_dir = os.path.join(os.path.dirname(base_input_dir), os.path.basename(base_input_dir) + "_out")
        print(f"Input is a directory: {base_input_dir}")
        print(f"Output directory set to: {base_output_dir}")
        glob_pattern = os.path.join(base_input_dir, "**", "*.txt")
        all_files = glob.glob(glob_pattern, recursive=True)
        file_paths = [fp for fp in all_files if not (fp.endswith(".grouped_entities.json") or fp.endswith(".annotated.txt"))]
        print(f"Found {len(file_paths)} .txt files to process.")
    elif os.path.isfile(input_path) and input_path.endswith(".txt"):
        file_paths = [os.path.abspath(input_path)]
        base_input_dir = os.path.dirname(file_paths[0])
        base_output_dir = base_input_dir 
        print(f"Input is a single file: {file_paths[0]}")
        print(f"Output directory set to: {base_output_dir}")
    else:
        print(f"Error: Input path \'{input_path}\' is not a valid directory or .txt file.")
        sys.exit(1)
        
    if not file_paths:
        print("No .txt files found to process.")
        sys.exit(0)
    
    try:
        processor = IntegratedNERProcessor()
    except Exception as e:
        print(f"Failed to initialize IntegratedNERProcessor: {e}")
        sys.exit(1)
        
    total_start_time = time.time()
    processed_count = 0

    for i, file_path in enumerate(file_paths):
        print(f"\n--- Processing file {i+1}/{len(file_paths)}: {file_path} ---")
        file_start_time = time.time()
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                original_text = f.read()
        except Exception as e:
            print(f"Error reading input file: {e}")
            continue 
        grouped_results = {}
        pessoa_entities_for_annotation = []
        try: 
            grouped_results, pessoa_entities_for_annotation,name_mapping = processor.process_text(original_text)
        except Exception as e:
            print(f"error {e}")
            grouped_results = {}
            pessoa_entities_for_annotation = []
        relative_path = os.path.relpath(file_path, start=base_input_dir)
        name_root = os.path.splitext(relative_path)[0]
        output_json_path = os.path.join(base_output_dir, name_root + ".grouped_entities.json")
        output_annotated_path = os.path.join(base_output_dir, name_root + ".annotated.txt")

        if grouped_results:
            save_grouped_entities(grouped_results, output_json_path)
            print(f"Found {len(grouped_results)} unique person groups. Saved JSON to: {output_json_path}")
        else:
            print("No person groups found or an error occurred during grouping.")

        if pessoa_entities_for_annotation:
            annotated_text = create_annotated_text(original_text, pessoa_entities_for_annotation,name_mapping)
            save_annotated_text(annotated_text, output_annotated_path)
            print(f"Saved annotated text to: {output_annotated_path}")
        else:
            print("No PESSOA entities found for annotation. Saving original text.")
            save_annotated_text(original_text, output_annotated_path)

        file_time = time.time() - file_start_time
        print(f"Finished processing in {file_time:.2f} seconds.")
        processed_count += 1

    total_time = time.time() - total_start_time
    print(f"\n\nFinished processing {processed_count} files in {total_time:.2f} seconds.")
    if processed_count > 0:
        avg_time = total_time / processed_count
        print(f"Average time per file: {avg_time:.2f} seconds.")

if __name__ == "__main__":
    try:
        import torch
        import transformers
        import fuzzywuzzy
    except ImportError as e:
        print(f"Error: Required library not found ({e}). Please install requirements:")
        print("pip install torch transformers fuzzywuzzy[speedup]")
        sys.exit(1)
    main()

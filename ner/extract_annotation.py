import re
import json
import sys

def extract_entities_from_annotated_text(annotated_text):
    entities = []
    original_text_parts = []
    current_original_pos = 0
    last_match_end = 0

    for match in re.finditer(r"<([^>]+)>", annotated_text):
        entity_text = match.group(1)
        tag_start_pos = match.start()
        tag_end_pos = match.end()

        # Append the text segment before this tag to original_text_parts
        text_before_tag = annotated_text[last_match_end:tag_start_pos]
        original_text_parts.append(text_before_tag)
        current_original_pos += len(text_before_tag)

        # Calculate original start and end for the current entity
        original_start = current_original_pos
        original_end = original_start + len(entity_text)

        entities.append({
            "text": entity_text,
            "original_start": original_start,
            "original_end": original_end
        })

        # Add the entity text itself to original_text_parts (as it's part of the original)
        original_text_parts.append(entity_text) # This is for reconstructing the original text, not for offset calculation here
        current_original_pos += len(entity_text) # Update current_original_pos with entity_text length

        last_match_end = tag_end_pos

    # Append any remaining text after the last tag
    remaining_text = annotated_text[last_match_end:]
    original_text_parts.append(remaining_text)

    reconstructed_original_text = "".join(original_text_parts) # This is not strictly needed for entity positions if calculated correctly
    
    # Corrected logic for original_text reconstruction and position calculation
    # Let's re-evaluate the position calculation to be more robust.
    # We can build the original text and map positions more directly.

    entities_corrected = []
    original_text_builder = []
    original_idx = 0
    annotated_idx = 0
    
    while annotated_idx < len(annotated_text):
        if annotated_text[annotated_idx] == '<':
            match = re.match(r"<([^>]+)>", annotated_text[annotated_idx:])
            if match:
                entity_text = match.group(1)
                tag_len = len(match.group(0)) # Length of <entity_text>
                
                start_original = original_idx
                original_text_builder.append(entity_text)
                original_idx += len(entity_text)
                end_original = original_idx
                
                entities_corrected.append({
                    "text": entity_text,
                    "original_start": start_original,
                    "original_end": end_original
                })
                annotated_idx += tag_len
            else:
                # Not a valid tag, treat as normal character (should not happen with <...>
                original_text_builder.append(annotated_text[annotated_idx])
                original_idx += 1
                annotated_idx += 1
        else:
            original_text_builder.append(annotated_text[annotated_idx])
            original_idx += 1
            annotated_idx += 1
            
    # original_text_final = "".join(original_text_builder)
    return entities_corrected, "".join(original_text_builder)

if __name__ == "__main__":
    # Example: python3 extract_annotation.py path/to/gabarito.txt path/to/teste/tipo
    #annotated_file_path = sys.argv[1] if len(sys.argv) > 1 else exit(1)
    #output_json_path = sys.argv[2] + "/extracted_manual_entities.json" if len(sys.argv) > 2 else exit(1)
    #original_text_output_path = sys.argv[2] + "/_original.txt" if len(sys.argv) > 2 else exit(1)
    #annotated_file_path = "/home/dudu/Graph-creation-with-html/testes/teste1/senado_r/13417_gabarito.txt"
    #output_json_path = "/home/dudu/Graph-creation-with-html/testes/teste1/senado_r/extracted_manual_entities.json"
    #original_text_output_path = "/home/dudu/Graph-creation-with-html/testes/teste1/senado_r/_original.txt"
    # Check if we got the right number of arguments
    if len(sys.argv) != 3:
        print("Usage: python extract_manual_annotations.py <input_file> <output_directory>")
        print("Example: python extract_manual_annotations.py 13417_gabarito.txt ./output")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2].rstrip('/')  # Remove trailing slash if present
    output_json_path = f"{output_dir}/extracted_manual_entities.json"
    original_text_output_path = f"{output_dir}/reconstructed_original_from_gabarito.txt"

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            annotated_content = f.read()
    except FileNotFoundError:
        print(f"Error: Annotated file not found at {input_file}")
        exit(1)

    extracted_entities, reconstructed_original = extract_entities_from_annotated_text(annotated_content)

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(extracted_entities, f, ensure_ascii=False, indent=4)
    
    with open(original_text_output_path, "w", encoding="utf-8") as f:
        f.write(reconstructed_original)

    print(f"Extracted {len(extracted_entities)} entities. Saved to {output_json_path}")
    print(f"Reconstructed original text saved to {original_text_output_path}")
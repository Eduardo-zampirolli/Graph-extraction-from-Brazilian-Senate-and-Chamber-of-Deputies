import json
import sys
from collections import OrderedDict
import sys

#extracted_entities_path = "/home/ubuntu/extracted_manual_entities.json"
#output_grouped_json_path = "/home/ubuntu/manual_gabarito_grouped_v3.json"
#Example: python3 create_manual.py path/teste/tipo/
extracted_entities_path = f"{sys.argv[1]}/extracted_manual_entities.json" if len(sys.argv) > 1 else exit(1)
output_grouped_json_path = f"{sys.argv[1]}/manual_grouped.json"
names_dict_path = f"{sys.argv[1]}/names_dict.txt"
canonical_name_map = {}
with open(names_dict_path, "r", encoding="utf-8") as file:
    for line in file:
        # Skip empty lines
        line = line.strip()
        if not line:
            continue
            
    # Split the line into key and value
        if ':' in line:
            key, value = line.split(':', 1)
            canonical_name_map[key.strip()] = value.strip()

canonical_name_map_raw_v1 = {
    "Alessandro Stefanutto": "Alessandro Stefanutto",
    "DAMARES ALVES": "DAMARES ALVES",
    "Damares": "DAMARES ALVES",
    "Deolane Bezerra": "Deolane Bezerra",
    "GABRIEL MURICCA GALÍPOLO": "GABRIEL MURICCA GALÍPOLO",
    "Gabriel": "GABRIEL MURICCA GALÍPOLO",
    "Gabriel Galípolo": "GABRIEL MURICCA GALÍPOLO",
    "Galípolo": "GABRIEL MURICCA GALÍPOLO",
    "HIRAN": "Hiran",
    "Helio Daher": "Helio Daher",
    "Hiran": "Hiran",
    "IZALCI LUCAS": "IZALCI LUCAS",
    "Izalci": "IZALCI LUCAS",
    "JAQUES WAGNER": "JAQUES WAGNER",
    "JULIANA MOZACHI SANDRI": "JULIANA MOZACHI SANDRI",
    "Jaques Wagner": "JAQUES WAGNER",
    "Jaques": "JAQUES WAGNER",
    "Ju": "JULIANA MOZACHI SANDRI",
    "Juliana": "JULIANA MOZACHI SANDRI",
    "Juliana Mozachi": "JULIANA MOZACHI SANDRI",
    "Juliana Sandri": "JULIANA MOZACHI SANDRI",
    "Lupi": "Lupi",
    "Nelsinho Trad": "Nelsinho Trad",
    "Omar Aziz": "Omar Aziz",
    "ROGÉRIO ANTÔNIO LUCCA": "ROGÉRIO ANTÔNIO LUCCA",
    "Regis Dudena": "Regis Dudena",
    "Rogério": "ROGÉRIO ANTÔNIO LUCCA",
    "Rogério Lucca": "ROGÉRIO ANTÔNIO LUCCA",
    "SORAYA THRONICKE": "SORAYA THRONICKE",
    "Soraya": "SORAYA THRONICKE",
    "Soraya Thronicke": "SORAYA THRONICKE"
}

# Ensure all distinct entities from the latest extraction are mapped.
# If any are missing from user's list, they will use text as canonical name (with a warning).

canonical_name_map_v1 = {k: v for k, v in canonical_name_map_raw_v1.items()}

try:
    with open(extracted_entities_path, "r", encoding="utf-8") as f:
        all_entities = json.load(f)
except FileNotFoundError:
    print(f"Error: Extracted entities file not found at {extracted_entities_path}", file=sys.stderr)
    sys.exit(1)
except json.JSONDecodeError:
    print(f"Error: Could not decode JSON from {extracted_entities_path}", file=sys.stderr)
    sys.exit(1)

if not isinstance(all_entities, list):
    print(f"Error: Expected a list of entities in {extracted_entities_path}, got {type(all_entities)}", file=sys.stderr)
    sys.exit(1)

grouped_entities_temp = {}

for entity in all_entities:
    if not isinstance(entity, dict) or "text" not in entity or "original_start" not in entity or "original_end" not in entity:
        print(f"Warning: Skipping invalid entity object: {entity}", file=sys.stderr)
        continue

    entity_text = entity["text"]
    original_start = entity["original_start"]
    original_end = entity["original_end"]
    score = 1.0 # For manual annotations, score is 1.0

    canonical_name = canonical_name_map.get(entity_text)

    if canonical_name is None:
        print(f"Warning: No canonical name mapping found for \'{entity_text}\'. Using text itself as canonical.", file=sys.stderr)
        canonical_name = entity_text 

    if canonical_name not in grouped_entities_temp:
        grouped_entities_temp[canonical_name] = []
    
    position_entry = [original_start, original_end, score]
    if position_entry not in grouped_entities_temp[canonical_name]:
        grouped_entities_temp[canonical_name].append(position_entry)

# Sort positions within each canonical name entry by start index
for canonical_name_key in grouped_entities_temp:
    grouped_entities_temp[canonical_name_key].sort(key=lambda x: x[0])

# Now, sort the canonical_name_key groups themselves
# Primary sort: alphabetical (A-Z) on canonical_name_key.lower()
# Secondary sort: length of canonical_name_key (descending)

sorted_grouped_items = sorted(
    grouped_entities_temp.items(), 
    key=lambda item: (-len(item[0]), item[0].lower())
)

# Create an OrderedDict to preserve the sort order for JSON output
final_grouped_entities = OrderedDict(sorted_grouped_items)

try:
    with open(output_grouped_json_path, "w", encoding="utf-8") as f:
        json.dump(final_grouped_entities, f, ensure_ascii=False, indent=4)
except IOError:
    print(f"Error: Could not write to output JSON file {output_grouped_json_path}", file=sys.stderr)
    sys.exit(1)

print(f"Successfully created sorted and grouped manual annotations JSON: {output_grouped_json_path}")
print(f"Number of canonical groups: {len(final_grouped_entities)}")

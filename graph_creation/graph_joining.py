import os
import sys
from fuzzywuzzy import fuzz
import glob
import networkx as nx
import re
from unidecode import unidecode # Import unidecode

class NameNormalizer:
    def __init__(self):
        # Maps a normalized name variation to its chosen canonical form (original casing)
        self.norm_to_canonical = {}
        # Tracks normalized names identified as having conflicts
        self.conflicts = set()

    def _normalize(self, name):
        """Robust normalization: remove titles, party/state, accents, punctuation, lowercase."""
        if not name: return ""
        # Remove party-state suffix like "- PT-CE" or "/PT-CE"
        name = re.sub(r"\s*[-/]\s*[A-Z]{2,}\s*-\s*[A-Z]{2}\s*\)?\s*$", "", name).strip()
        # Remove content within parentheses if it seems like party/bloc info
        name = re.sub(r"\s*\((?:Bloco|Partido|\w+/)?([A-Z]+)\s*-\s*([A-Z]{2})\)\s*$", "", name, flags=re.IGNORECASE).strip()
        # Remove common titles (case-insensitive)
        titles = ["sr", "sra", "dr", "dra", "deputado", "deputada", "senador", "senadora", "presidente"]
        temp_name = name.lower()
        for title in titles:
             # Check if title is at the beginning followed by space or dot
            if temp_name.startswith(title + " ") or temp_name.startswith(title + "."):
                name = re.sub(r"^" + re.escape(title) + r"\.?\s+", "", name, count=1, flags=re.IGNORECASE).strip()
                break # Remove only the first occurrence
                
        # Remove accents using unidecode and convert to lowercase
        name = unidecode(name).lower()
        
        # Remove punctuation (keep internal hyphens if needed, but removing all here)
        name = re.sub(r"[.,;:!?()\"\\]", "", name)
        # Normalize whitespace
        name = " ".join(name.split())
        
        # Return None if normalization results in empty or too short string
        if not name or len(name) < 2:
            return None
            
        return name

    def get_canonical_name(self, original_name):
        """Gets the canonical name for a given name, handling variations and conflicts."""
        if not original_name: return None

        normalized_name = self._normalize(original_name)
        # If normalization fails (e.g., results in empty string), return original
        if not normalized_name: 
            # print(f"Normalization failed for: {original_name}") # Debug
            return original_name 

        # If this normalized name is known to conflict, return the original
        if normalized_name in self.conflicts:
            # print(f"Conflict known for {normalized_name}, returning original: {original_name}") # Debug
            return original_name

        # If this normalized name already has a canonical form, update originals and return it
        if normalized_name in self.norm_to_canonical:
            canonical_entry = self.norm_to_canonical[normalized_name]
            canonical_entry["original_names"].add(original_name)
            # Update canonical if current original is longer
            if len(original_name) > len(canonical_entry["canonical_name"]):
                canonical_entry["canonical_name"] = original_name
            return canonical_entry["canonical_name"]

        # --- Find potential matches among existing canonical names --- 
        potential_matches = []
        # Compare against the normalized versions (keys) of existing canonical clusters
        for existing_norm, canonical_entry in self.norm_to_canonical.items():
            # Skip comparison if the existing one is a conflict
            if existing_norm in self.conflicts: continue

            # Calculate similarity score (using token_set_ratio as primary)
            similarity = fuzz.token_set_ratio(normalized_name, existing_norm)

            # Define match conditions (Simplified: High similarity needed)
            is_match = False
            if similarity >= 85:
                is_match = True

            if is_match:
                potential_matches.append((existing_norm, similarity))

        # --- Decide based on matches --- 
        
        # Case 1: No good matches found -> This is a new canonical name
        if not potential_matches:
            new_entry = {"canonical_name": original_name, "original_names": {original_name}}
            self.norm_to_canonical[normalized_name] = new_entry
            # print(f"New canonical: 	{normalized_name} -> {original_name}") # Debug
            return original_name

        # Case 2: Exactly one good match found -> Merge with existing canonical
        elif len(potential_matches) == 1:
            matched_norm, _ = potential_matches[0]
            existing_canonical_entry = self.norm_to_canonical[matched_norm]
            existing_canonical_entry["original_names"].add(original_name)
            new_canonical = max(existing_canonical_entry["original_names"], key=len)
            existing_canonical_entry["canonical_name"] = new_canonical
            self.norm_to_canonical[normalized_name] = existing_canonical_entry 
            # print(f"Merged: 	{normalized_name} ({original_name}) with {matched_norm} -> {new_canonical}") # Debug
            return new_canonical

        # Case 3: Multiple good matches found -> Conflict!
        else:
            potential_matches.sort(key=lambda x: x[1], reverse=True)
            if len(potential_matches) >= 2 and (potential_matches[0][1] - potential_matches[1][1]) >= 10: 
                matched_norm, _ = potential_matches[0]
                existing_canonical_entry = self.norm_to_canonical[matched_norm]
                existing_canonical_entry["original_names"].add(original_name)
                new_canonical = max(existing_canonical_entry["original_names"], key=len)
                existing_canonical_entry["canonical_name"] = new_canonical
                self.norm_to_canonical[normalized_name] = existing_canonical_entry
                # print(f"Conflict resolved (top match): 	{normalized_name} ({original_name}) with {matched_norm} -> {new_canonical}") # Debug
                return new_canonical
            else:
                # print(f"Conflict detected for: {normalized_name} ({original_name}). Matches: {potential_matches}") # Debug
                self.conflicts.add(normalized_name)
                return original_name

def split_into_speeches(text):
    """Split text into individual speeches based on speaker intro patterns."""
    pattern = r"(?=\b(?:O|A)\s+SR(?:A)?\.\s+(?:PRESIDENTE|DEPUTADO|DEPUTADA|SENADOR|SENADORA|DR|DRA|[A-ZÀ-Ú]+(?:\.\s*)?)\b)"
    speeches = re.split(pattern, text, flags=re.IGNORECASE)
    return [s.strip() for s in speeches if s and s.strip()]

# --- CORRECTED: Pass normalizer instance --- 
def extract_speaker_and_mentions(speech_text, normalizer):
    """Extract speaker and mentions from a single speech using PESSOA tags."""
    pessoa_tags = re.findall(r"<PESSOA:([^>]+)>", speech_text)
    if not pessoa_tags:
        return None, []

    speaker_original = pessoa_tags[0]
    # --- CORRECTED: Call method on instance --- 
    speaker_canonical = normalizer.get_canonical_name(speaker_original)

    mentions_canonical = []
    for i, mentioned_original in enumerate(pessoa_tags):
        if i == 0: continue 
        # --- CORRECTED: Call method on instance --- 
        mentioned_canonical = normalizer.get_canonical_name(mentioned_original)
        if mentioned_canonical and mentioned_canonical != speaker_canonical:
            mentions_canonical.append(mentioned_canonical)
            
    return speaker_canonical, list(set(mentions_canonical))

def create_graph(input_dir, output_dir="speech_graph_revised.gexf"):
    """Process all text files and build mention graph using refined normalization/grouping."""
    # --- CORRECTED: Create instance of normalizer --- 
    normalizer = NameNormalizer()
    
    graph = nx.DiGraph()
    node_id_counter = 0 
    node_map = {} # Map canonical names to node IDs

    print(f"Processing files in: {input_dir}")
    if not os.path.isdir(input_dir):
        print(f"Error: Input directory not found: {input_dir}")
        return None
        
    file_list = sorted(glob.glob(os.path.join(input_dir, "*.txt")))
    if not file_list:
        print(f"Warning: No .txt files found in {input_dir}")

    processed_files = 0
    for filename in file_list:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                text = f.read()
            processed_files += 1
        except Exception as e:
            print(f"Error reading file {filename}: {e}")
            continue 

        speeches = split_into_speeches(text)
        
        for speech in speeches:
            # --- CORRECTED: Pass normalizer instance --- 
            speaker, mentions = extract_speaker_and_mentions(speech, normalizer)
            
            if not speaker:
                continue

            # Ensure speaker node exists
            if speaker not in node_map:
                node_id_counter += 1
                node_map[speaker] = node_id_counter
                graph.add_node(speaker, id=node_id_counter, label=speaker)

            # Process mentions
            for mentioned in mentions:
                if not mentioned: continue 
                
                # Ensure mentioned node exists
                if mentioned not in node_map:
                    node_id_counter += 1
                    node_map[mentioned] = node_id_counter
                    graph.add_node(mentioned, id=node_id_counter, label=mentioned)
                
                # Add or update edge weight
                if graph.has_edge(speaker, mentioned):
                    graph[speaker][mentioned]["weight"] += 1
                else:
                    graph.add_edge(speaker, mentioned, weight=1)
                    
    print(f"\nProcessed {processed_files} files.")
    # Save graph and print summary
    try:
        nx.write_gexf(graph, output_dir)
        print(f"Graph saved to {output_dir}")
        print(f"Total nodes (unique canonical names): {graph.number_of_nodes()}")
        print(f"Total edges (mentions): {graph.number_of_edges()}")
        #print(f"Total mention weight (sum of weights): {graph.size(weight=\'weight\')}")
    except Exception as e:
        print(f"Error saving graph to {output_dir}: {e}")

    return graph

def main():
    #python3 graph_joining.py path/to/type/anotacoes/year path/to/graph/type
    if len(sys.argv) < 3:
        print("Usage: python3 t3_revised.py <input_directory_path>")
        input_dir = "/home/eduardo/Documentos/est_dir/Senado/senado_r_anotacoes/2024"
        output_dir = "/home/eduardo/Graph-creation-with-html/Graph-creation-with-html/graphs/senado_r"
        print(f"Warning: No input directory provided. Using current directory: {input_dir}")
        if not os.path.isdir(input_dir):
             print(f"Error: Current directory not found?")
             return
    else:
        input_dir = sys.argv[1]
        output_dir = sys.argv[2]

    input_dir_name = os.path.basename(os.path.abspath(input_dir))
    output_filename = f"{output_dir}/grafo_{input_dir_name}.gexf"
        
    create_graph(input_dir, output_filename)

if __name__ == "__main__":
    # Check dependencies
    try: import networkx
    except ImportError: print("Error: networkx not found. pip install networkx"); sys.exit(1)
    try: from unidecode import unidecode
    except ImportError: print("Error: unidecode not found. pip install unidecode"); sys.exit(1)
    try: import fuzzywuzzy
    except ImportError: print("Error: fuzzywuzzy not found. pip install fuzzywuzzy python-Levenshtein"); sys.exit(1)
        
    main()


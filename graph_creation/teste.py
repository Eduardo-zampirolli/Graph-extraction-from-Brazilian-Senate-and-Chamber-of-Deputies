import os
import sys
from fuzzywuzzy import fuzz
import glob
import json
import networkx as nx
import re


class NameNormalizer:
    def __init__(self):
        self.name_map = {}  # Maps variations to canonical names
    
    def get_canonical_name(self, name):
        """Get or create canonical name with fuzzy matching"""
        if not name:
            return None
            
        # Check for existing similar names (case insensitive)
        for existing_name in self.name_map:
            if fuzz.ratio(name.lower(), existing_name.lower()) >= 85:
                if len(existing_name >= name):
                    return existing_name
                self.name_map 
                return name
                
        # New unique name
        self.name_map[name] = name
        return name
    
def split_into_speeches(text):
    """Split text into individual speeches"""
    # Split on speaker patterns (handling both formats)
    return re.split(r'(?=O SR\.|A SRA\.|O SR. PRESIDENTE\.|A SRA. PRESIDENTE)', text)

def create_graph(input_dir, output_file='speech_graph.gexf'):
    """Process all text files and build mention graph"""
    normalizer = NameNormalizer()
    graph = nx.DiGraph()
    cont = 100
    for filename in sorted(f for f in os.listdir(input_dir) if f.endswith('.txt')):
        with open(os.path.join(input_dir, filename), 'r', encoding='utf-8') as f:
            text = f.read()
            
            for speech in filter(None, split_into_speeches(text)):
                speaker, mentions = extract_speaker_and_mentions(speech, normalizer)
                if not speaker or not mentions:
                    continue
                
                # Ensure speaker node exists
                if speaker not in graph:
                    cont+=1
                    graph.add_node(speaker, id=cont, source_file=filename)
                
                # Process mentions
                for mentioned in mentions:
                    if mentioned not in graph:
                        cont+=1
                        graph.add_node(mentioned, id=cont, source_file=filename)
                    
                    # Update edge weight
                    if graph.has_edge(speaker, mentioned):
                        graph[speaker][mentioned]['weight'] += 1
                    else:
                        graph.add_edge(speaker, mentioned, weight=1, source_file=filename)
    
    # Save graph and print summary
    nx.write_gexf(graph, output_file)
    print(f"Graph saved to {output_file}")
    print(f"Total nodes: {len(graph.nodes(data=True))}")
   
    print(f"Total mentions: {len(graph.edges())}")
    
    return graph


def group_similar_persons(entities):
        '''Grouping the same entity but with different name'''
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
                if is_similar(raw_word, canonical):
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

def extract_speaker_and_mentions(speech_text, normalizer):
    """Extract speaker and mentions from a single speech"""
    # Extract speaker name from PESSOA tag if available
    speaker_match = re.search(r'<PESSOA:([^>]+)>', speech_text)
    if not speaker_match:
        return None, []
    
    # Get whichever group matched (either group 1 or group 2)
    speaker_name = speaker_match.group(1)# or speaker_match.group(2)
    speaker = normalizer.get_canonical_name(speaker_name) if speaker_name else None
    
    # Extract all mentions from PESSOA tags
    mentions = []
    for match in re.finditer(r'<PESSOA:([^>]+)>', speech_text):
        mentioned_name = normalizer.get_canonical_name(match.group(1))
        if mentioned_name and mentioned_name != speaker:  # Exclude self-mentions
            mentions.append(mentioned_name)
    
    return speaker, mentions#list(set(mentions))  # Remove duplicates


def is_similar(name1, name2, threshold=85):
    """Check if names are similar enough to merge"""
    if not name1 or not name2: return False
    return fuzz.token_set_ratio(name1, name2) >= threshold

def main():
    #'pyhton3 teste.py /path/to/type/'
    type = '/home/eduardo/Documentos/est_dir/Camara/camara_anotacoes'
    for year in os.listdir(type):
        year_path = os.path.join(type, year)  
        graph=create_graph(year_path, f'{year}.gexf')
        
    return
if __name__=="__main__":
    main()
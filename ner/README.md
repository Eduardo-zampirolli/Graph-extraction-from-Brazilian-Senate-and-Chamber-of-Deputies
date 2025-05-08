
# Detailed Guide for `training_grouped_final.py`

This document provides a comprehensive explanation of the Python script `training_grouped_final.py`. The script is designed to perform Named Entity Recognition (NER) specifically for person entities ("PESSOA") within Portuguese text files. It combines rule-based methods with a pre-trained transformer model, merges fragmented entity mentions, and groups similar entity names together.

## 1. Imports

The script begins by importing necessary libraries:

```python
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
import torch
import sys
import numpy as np
import json
import math
import os
import glob
import time
import re
from fuzzywuzzy import fuzz
from unicodedata import normalize
```

- **`transformers`**: This is the core library from Hugging Face used for accessing pre-trained models and pipelines. 
    - `pipeline`: A high-level abstraction for using models for specific tasks (like NER).
    - `AutoTokenizer`: Automatically loads the correct tokenizer associated with a pre-trained model.
    - `AutoModelForTokenClassification`: Automatically loads the correct model architecture for token classification tasks (like NER).
- **`torch`**: The PyTorch library, used as the backend for the transformer model. It's used here to check for GPU availability (`torch.cuda.is_available()`) and potentially for managing tensor operations (though `pipeline` abstracts most of this).
- **`sys`**: Provides access to system-specific parameters and functions, used here for handling command-line arguments (`sys.argv`) and exiting the script (`sys.exit`).
- **`numpy`**: A fundamental package for numerical computation. It's used implicitly by the model and explicitly in `convert_numpy_types` to handle data types before JSON serialization.
- **`json`**: Used for reading and writing data in JSON format, specifically for the `.entities.json` output file.
- **`math`**: Provides mathematical functions, used here for `math.ceil` in the text chunking logic.
- **`os`**: Provides a way of using operating system dependent functionality, used for path manipulation (`os.path.join`, `os.path.dirname`, `os.path.basename`, `os.path.splitext`, `os.path.abspath`, `os.path.relpath`), checking file/directory existence (`os.path.isdir`, `os.path.isfile`), and creating directories (`os.makedirs`).
- **`glob`**: Used for finding files matching a specific pattern (e.g., finding all `.txt` files in a directory recursively).
- **`time`**: Used for timing the execution of different parts of the script (model loading, file processing).
- **`re`**: The regular expression library, used for rule-based entity extraction (`_rule_based_ner`) and name normalization (`_normalize_for_comparison`).
- **`fuzzywuzzy`**: Used to compare the similarity between strings, useful to group entities with different, but similar, names in the text

## 2. The `IntegratedNERProcessor` Class

This class encapsulates all the logic related to extracting, merging, and grouping person entities.

```python
class IntegratedNERProcessor:
    # ... (class content)
```

### 2.1. `__init__(self, model_name="pierreguillou/ner-bert-base-cased-pt-lenerbr")`

This is the constructor method, executed when an object of the class is created.

```python
    def __init__(self, model_name="pierreguillou/ner-bert-base-cased-pt-lenerbr"):
        # ... (initialization logic)
```

- **Purpose**: Initializes the NER extractor by loading the specified pre-trained model and tokenizer, setting up the NER pipeline, determining the computation device (GPU or CPU), and compiling a regular expression for rule-based extraction.
- **Parameters**:
    - `model_name` (str, optional): The identifier of the Hugging Face model to use. Defaults to `"pierreguillou/ner-bert-base-cased-pt-lenerbr"`, a model trained for NER on Portuguese text.
- **Logic**:
    1.  Stores the `model_name`.
    2.  Prints a message indicating model loading is starting and records the start time.
    3.  Loads the tokenizer associated with the `model_name` using `AutoTokenizer.from_pretrained()`.
    4.  Loads the pre-trained model for token classification using `AutoModelForTokenClassification.from_pretrained()`.
    5.  Checks if a CUDA-enabled GPU is available using `torch.cuda.is_available()`. Sets `self.device` to `0` (for the first GPU) if available, otherwise `-1` (for CPU).
    6.  Prints the device being used (GPU or CPU). This uses the workaround for the f-string syntax issue.
    7.  Retrieves the maximum sequence length supported by the tokenizer (`self.tokenizer.model_max_length`). It includes a check to ensure this value is a reasonable integer (between 1 and 1024), defaulting to 512 if it's invalid or missing. This `max_seq_len` is important for the chunking logic later.
    8.  Initializes the Hugging Face NER `pipeline`. 
        - Task is set to `"ner"`.
        - The loaded `model` and `tokenizer` are provided.
        - `aggregation_strategy="simple"` tells the pipeline to automatically group word pieces (sub-tokens) belonging to the same entity.
        - The determined `device` (GPU or CPU) is specified.
        - `framework="pt"` specifies PyTorch as the backend.
    9.  Calculates and prints the time taken to load the model.
    10. Compiles a regular expression (`self.title_regex`) to find names following Portuguese titles like "O SR." (Mr.) or "A SRA." (Mrs.). It looks for the title followed by a sequence of capitalized words, potentially including common connectors like "de", "da", "do". The `re.IGNORECASE` flag makes the title matching case-insensitive.

## 2.2. `_rule_based_ner(self, text)`
- **This function was not used in this version, but it is useful if, for some reason, any speaker was not found by the model or if we want to collect some information in the name description, like political party or state**
```python
    def _rule_based_ner(self, text):
        # ... (rule-based extraction logic)
```

- **Purpose**: Extracts person names based solely on the pre-compiled regular expression (`self.title_regex`) that looks for names following "O SR." or "A SRA.". Also add party and state from the entity
- **Parameters**:
    - `text` (str): The input text to search within.
- **Returns**: 
    - `rule_entities` (list): A list of dictionaries, where each dictionary represents a person entity found by the rule. Each dictionary contains:
        - `entity_group`: Always "PESSOA".
        - `score`: Always 1.0 (indicating high confidence from the rule).
        - `word`: The extracted name string.
        - `start`: The starting character index of the name in the original text.
        - `end`: The ending character index (exclusive) of the name in the original text.
        - `source`: Always "rule".
        - `matadata`:
            - `party`
            - `state`
            - `title`: None or PRESIDENTE
- **Logic**:
    1. Initializes an empty list `rule_entities`.
    2. Iterates through all matches found by `self.title_regex.finditer(text)`.
    3. For each match:
        - Extracts the captured name part (group 1 of the regex) and removes leading/trailing whitespace (`match.group(1).strip()`).
        - Performs some basic cleanup on the extracted name:
            - If a period (`.`) exists within the name, it tries to find if the period is followed by whitespace and another capital letter, parenthesis, newline, or end-of-string. If so, it assumes the period marks the end of the name and truncates the name before the period.
            - From the parenthesized we colect the name (if president), party and state.
        - Checks if the cleaned name is valid (not empty and longer than 1 character).
        - If valid, creates a dictionary with the entity details (group, score, word, start/end indices, source) and appends it to `rule_entities`.
    4. Returns the `rule_entities` list.

### 2.3. `extract_persons(self, text)`

```python
    def extract_persons(self, text):
        # ... (main extraction, merging, and grouping logic)
```

- **Purpose**: This is the main method orchestrating the entire entity extraction, merging, and grouping process for a given text.
- **Parameters**:
    - `text` (str): The input text to process.
- **Returns**: 
    - A tuple containing two items:
        1. `merged_persons` (list): A list of dictionaries representing person entities *after* the initial merging step (`_merge_split_persons`) but *before* the final grouping step (`_group_similar_persons`). This list is used for creating the `.annotated.txt` file.
        2. `grouped_persons_dict` (dict): A dictionary where keys are the canonical person names and values are lists of `(start, end)` tuples representing all mentions of that person. This dictionary is saved to the `.entities.json` file.
- **Logic**:
    1.  **Error Handling**: Wraps the entire process in a `try...except` block to catch and report any errors during processing, returning empty results (`[], {}`) if an error occurs.
    2.  **Rule-Based Extraction**: Calls `self._rule_based_ner(text)` to get entities found by the title rule.
    3.  **Model-Based Extraction (Chunking)**:
        - Initializes an empty list `model_entities`.
        - Defines a `chunk_char_size` (e.g., 400 characters) and an `overlap_size` (e.g., 100 characters). The overlap ensures that entities spanning chunk boundaries are likely captured completely in at least one chunk.
        - **If the text is longer than `chunk_char_size`**: 
            - Calculates the number of chunks needed using `math.ceil` based on the text length, chunk size, and overlap.
            - Iterates through the calculated number of chunks:
                - Determines the `chunk_start` and `chunk_end` indices for the current chunk, considering the overlap. Includes checks to prevent invalid indices (negative start, start >= end).
                - Extracts the `chunk_text`.
                - Calls the `self.ner_pipeline` on the `chunk_text` within a `try...except` block (to handle potential pipeline errors) and using `torch.no_grad()` (to improve efficiency by disabling gradient calculations).
                - Iterates through the raw entities returned by the pipeline for the chunk:
                    - If an entity is a "PESSOA":
                        - Adjusts the `start` and `end` indices by adding the `chunk_start` offset to make them relative to the original text.
                        - **Crucially, verifies that the adjusted indices are valid** (within the bounds of the original text) before trying to extract the `word` from the original text using these indices.
                        - If indices are valid, extracts the `word`, sets the `source` to "model", and appends the entity dictionary to `model_entities`.
                        - If indices are invalid, prints a warning and skips the entity.
        - **If the text is shorter than `chunk_char_size`**: 
            - Processes the entire text directly with `self.ner_pipeline` (also within `try...except` and `torch.no_grad()`).
            - Filters for "PESSOA" entities, verifies indices, extracts the `word`, sets the `source`, and appends to `model_entities`.
    4.  **Integration of Rule and Model Entities**: 
        - Initializes an empty list `combined_entities` and a set `covered_spans`.
        - Adds all `rule_entities` to `combined_entities` and their spans `(start, end)` to `covered_spans`.
        - Iterates through `model_entities`:
            - Checks if the model entity significantly overlaps with or is contained within any span already covered by a rule entity.
            - If it's *not* covered, adds the model entity to `combined_entities` and its span to `covered_spans`.
        - This step prioritizes rule-based entities and avoids adding duplicate or highly overlapping model entities.
    5.  **Merging**: Calls `self._merge_split_persons(combined_entities, text)` to merge adjacent or slightly overlapping fragments that likely belong to the same name mention (e.g., "Gilvan" and "da Federal" detected separately).
    6.  **Grouping**: Calls `self._group_similar_persons(merged_persons)` on the result of the merging step. This function groups different variations of the same person's name (e.g., "Gilvan da Federal", "Gilvan", "Gilvan da Federal.") under a single canonical name.
    7.  **Return**: Returns the `merged_persons` list (from step 5) and the `grouped_persons_dict` (from step 6).



### 2.4. `_merge_split_persons(self, person_entities, original_text)`

```python
    def _merge_split_persons(self, person_entities, original_text):
        # ... (merging logic)
```

- **Purpose**: Merges adjacent or slightly overlapping person entities that were likely split during the initial detection phase (e.g., "Jair" and "Bolsonaro" detected as separate entities). It aims to combine these fragments into a single, more complete name mention.
- **Parameters**:
    - `person_entities` (list): The list of person entity dictionaries (from both rule-based and model-based extraction, after initial filtering).
    - `original_text` (str): The full original text, needed to check characters between potential merge candidates.
- **Returns**: 
    - `final_merged` (list): A list of dictionaries representing the merged person entities. Entities that couldn't be merged are passed through unchanged. This list also undergoes a final deduplication based on exact span and word.
- **Logic**:
    1.  Handles the case of an empty input list.
    2.  Sorts the input `person_entities` primarily by their `start` position and secondarily by `end` position (descending, so longer entities come first in case of same start). This ensures processing in text order.
    3.  Initializes an empty list `merged` to store the results.
    4.  Iterates through the `sorted_entities` using a `while` loop and an index `i`.
    5.  For each `current` entity at index `i`:
        - Skips invalid entities (missing `word` or invalid indices).
        - Initializes `best_start`, `best_end`, `best_score`, and `best_text` based on the `current` entity.
        - Initializes `last_merged_idx` to `i`.
        - Enters an inner `while` loop (index `j`) to look ahead at subsequent entities (`next_entity`).
        - **Checks for Merge Candidates**: 
            - Skips invalid `next_entity`.
            - Breaks the inner loop if `next_entity` starts too far after the current `best_end` (more than 5 characters gap).
            - Skips `next_entity` if it's fully contained within the current `best_span`.
            - Calculates the `potential_end` and `potential_text` if `current` and `next_entity` were merged.
            - **Checks Validity of Merge**: 
                - Ensures the potential merged name isn't excessively long (<= 60 characters).
                - Examines the `text_between` the `best_end` of the current entity and the `start` of the `next_entity`.
                - Determines if the merge is valid (`is_valid_connector`) based on these conditions:
                    - Entities overlap or touch (`next_entity["start"] <= best_end`).
                    - The text between contains only allowed characters (space, hyphen, tab).
                    - The text between consists of 1 or 2 allowed connector words ("de", "da", "do", "dos", "das", "e").
                - **If the merge is valid**: Updates `best_end`, `best_score` (taking the max), `best_text`, and crucially, updates `last_merged_idx` to `j`. Increments `j` to consider the *next* entity for further merging with the now-extended span.
                - **If the merge is invalid**: Breaks the inner loop, as no further merging is possible with `next_entity`.
    6.  After the inner loop finishes (either by breaking or reaching the end), it means the `current` entity (potentially extended by merging) is complete.
    7.  Normalizes the case of the `best_text` using `_normalize_name_case()`.
    8.  Checks if the resulting `normalized_text` is a valid name using `_is_valid_name()`.
    9.  If valid, creates the merged entity dictionary and appends it to the `merged` list.
    10. Advances the outer loop index `i` to `last_merged_idx + 1`, effectively skipping over the entities that were just merged into the current one.
    11. **Final Deduplication**: After the main loop, iterates through the `merged` list and uses a `set` (`seen_spans`) to remove any exact duplicates based on `(start, end, word)`. Appends unique entities to `final_merged`.
    12. Returns `final_merged`.

### 2.5. `_is_valid_name(self, name)`

```python
    def _is_valid_name(self, name):
        # ... (validation logic)
```

- **Purpose**: A helper function to perform basic checks on a potential merged name string to see if it's likely a valid person name.
- **Parameters**:
    - `name` (str): The name string to validate.
- **Returns**: 
    - `True` if the name seems valid, `False` otherwise.
- **Logic**: Returns `False` if the name is:
    - Empty or shorter than 2 characters.
    - Contains no alphabetic characters.
    - Contains more than 7 words (heuristic to avoid overly long, likely incorrect merges).
    - Is exactly one of the common titles or connectors (after lowercasing).
    Otherwise, returns `True`.

### 2.6. `_normalize_name_case(self, name)`

```python
    def _normalize_name_case(self, name):
        # ... (case normalization logic)
```

- **Purpose**: Normalizes the capitalization of a given name string according to common conventions for Portuguese names.
- **Parameters**:
    - `name` (str): The name string to normalize.
- **Returns**: 
    - The name string with normalized capitalization.
- **Logic**:
    1. Handles empty input.
    2. Splits the name into parts (words).
    3. Iterates through each part:
        - If the lowercase part is a common connector ("de", "da", "do", etc.), keeps it lowercase.
        - Otherwise, handles hyphenated sub-parts:
            - Capitalizes the first letter of each sub-part and lowercases the rest (e.g., "JOÃO-BOSCO" -> "João-Bosco").
            - Handles all-caps parts (e.g., "SILVA" -> "Silva").
            - Preserves single uppercase letters (e.g., "J. R. R.").
    4. Joins the processed parts back together with spaces.




### 2.7. `_normalize_for_comparison(self, name)`

```python
    def _normalize_for_comparison(self, name):
        # ... (normalization for comparison logic)
```

- **Purpose**: Prepares a name string for similarity comparison by converting it to lowercase, removing common titles, stripping trailing punctuation, and normalizing whitespace. This is different from `_normalize_name_case` which focuses on proper capitalization for the final output.
- **Parameters**:
    - `name` (str): The name string to normalize.
- **Returns**: 
    - The normalized name string, suitable for comparison.
- **Logic**:
    1. Converts the name to lowercase and removes leading/trailing whitespace.
    2. Defines a list of common `titles` to remove.
    3. Iterates through the `titles` and uses `re.sub()` with word boundaries (`\b`) to remove them from the name string. This ensures only whole words are removed (e.g., doesn't remove "dr" from "drive").
    4. Removes any trailing periods or commas using `rstrip(". ,")`. **This step is crucial for handling cases like "Gilvan da Federal." vs "Gilvan da Federal"**. 
    5. Normalizes internal whitespace by splitting the string and rejoining with single spaces (`" ".join(name.split())`).
    6. Returns the fully normalized string.

### 2.8. `_is_similar(self, name1, name2)`

```python
    def _is_similar(self, name1, name2):
        # ... (similarity check logic)
```

- **Purpose**: Determines if two name strings likely refer to the same person based on a simple similarity check after normalization.
- **Parameters**:
    - `name1` (str): The first name string.
    - `name2` (str): The second name string.
- **Returns**: 
    - `True` if the names are considered similar, `False` otherwise.
- **Logic**:
    1. Normalizes both `name1` and `name2` using `self._normalize_for_comparison()`.
    2. Returns `False` if either normalized name is empty.
    3. Performs a simple substring check: returns `True` if `norm_name1` is contained within `norm_name2` or vice versa. This effectively handles cases like comparing a full name ("Erika Kokay") with a partial name ("Erika").
    4. Includes commented-out code suggesting a potential future enhancement using fuzzy matching libraries (like `fuzzywuzzy`) for more sophisticated similarity checks if needed.

### 2.9. `_group_similar_persons(self, entities)`

```python
    def _group_similar_persons(self, entities):
        # ... (grouping logic)
```

- **Purpose**: This is the core function that implements the entity grouping logic requested by the user. It takes the list of merged person entities and groups mentions that refer to the same person, even if the names are slightly different (e.g., partial names, names with titles removed, names with/without trailing punctuation).
- **Parameters**:
    - `entities` (list): The list of person entity dictionaries obtained after the `_merge_split_persons` step.
- **Returns**: 
    - `final_grouped` (dict): A dictionary where keys are the chosen canonical names and values are lists of `(start, end)` position tuples for all mentions associated with that canonical name. The position list is sorted by the start index.
- **Logic**:
    1. Handles the case of an empty input list.
    2. Sorts the input `entities` primarily by the length of the `word` (descending, so longer names come first) and secondarily alphabetically. This helps in selecting the longest form as the initial canonical name for a group.
    3. Initializes two dictionaries:
        - `grouped_entities`: Temporarily stores `{canonical_name: [(start, end, original_word), ...]}`.
        - `canonical_map`: Stores `{found_variation: canonical_name}` to quickly find the canonical name for any encountered variation.
    4. Iterates through the `sorted_entities`:
        - Gets the `name` (the `word` from the entity dictionary).
        - Stores the position info `(start, end, original_word)`.
        - **Checks `canonical_map`**: If this `name` variation has already been seen and mapped to a canonical name, it adds the current `pos_info` to the list for that canonical name in `grouped_entities` (avoiding duplicates) and continues to the next entity.
        - **If the name is new**: 
            - Sets `found_match` to `False`.
            - Iterates through the `existing_canonicals` names already in `grouped_entities`.
            - Uses `self._is_similar()` to compare the current `name` with each `canonical_name`.
            - **If a similar canonical name is found**: 
                - Sets `found_match` to `True`.
                - Chooses the longer of the two similar names (`name` vs. `canonical_name`) as the `chosen_canonical` name.
                - **Handles Canonical Name Change**: If the *current* `name` is chosen as the new canonical name (because it's longer than the existing one), it means the group needs to be renamed. It `pop`s the old group from `grouped_entities`, adds its positions to the new group under `chosen_canonical`, and updates the `canonical_map` for all variations previously pointing to the old canonical name, making them point to the new `chosen_canonical` name.
                - Adds the current entity's `pos_info` to the list for the `chosen_canonical` name in `grouped_entities` (avoiding duplicates).
                - Maps the current `name` variation to the `chosen_canonical` name in `canonical_map`.
                - Breaks the inner loop (no need to compare with other canonicals).
            - **If no similar canonical name is found**: 
                - This `name` starts a new group.
                - Maps the `name` to itself in `canonical_map`.
                - Adds the `pos_info` to a new list under `name` in `grouped_entities`.
    5. **Final Formatting**: After iterating through all entities, creates the `final_grouped` dictionary:
        - Iterates through the `grouped_entities` dictionary.
        - For each `canonical` name and its list of `positions` `[(start, end, original_word), ...]`: 
            - Sorts the `positions` list based on the `start` index.
            - Creates a new list containing only the `(start, end)` tuples.
            - Assigns this list of tuples to the `canonical` key in `final_grouped`.
    6. Returns `final_grouped`.

## 3. Standalone Functions

These functions are defined outside the class and perform specific tasks related to annotation, data conversion, and file processing.

### 3.1. `annotate_text(text, entities)`

```python
def annotate_text(text, entities):
    # ... (annotation logic)
```

- **Purpose**: Creates an annotated version of the original text where person entities are marked with `[PESSOA:Name]`. **Important**: This function uses the `merged_entities` list returned by `extract_persons`, which represents entities *before* the final grouping step.
- **Parameters**:
    - `text` (str): The original input text.
    - `entities` (list): The list of entity dictionaries (typically the `merged_persons` list).
- **Returns**: 
    - `annotated_text` (str): The text with PESSOA entities annotated.
- **Logic**:
    1. Initializes an empty string `annotated_text` and `current_pos = 0`.
    2. Filters out invalid entities (missing `start` or `end`).
    3. Sorts the valid `entities` by their `start` position.
    4. Iterates through the `sorted_entities`:
        - Gets `start` and `end` indices.
        - Skips entities that overlap significantly with already processed text (`start < current_pos`).
        - Skips invalid entities (`end <= start`).
        - Appends the text segment from `current_pos` up to the entity's `start`.
        - Appends the annotation tag `[PESSOA:{entity_word}]`, getting the `entity_word` from the dictionary.
        - Updates `current_pos` to the entity's `end`.
    5. After the loop, appends any remaining text from `current_pos` to the end.
    6. Returns the `annotated_text`.

### 3.2. `convert_numpy_types(obj)`

```python
def convert_numpy_types(obj):
    # ... (type conversion logic)
```

- **Purpose**: Recursively converts NumPy data types (like `np.integer`, `np.floating`, `np.ndarray`) within a nested data structure (like dictionaries or lists) into standard Python types (`int`, `float`, `list`). This is necessary because the default `json.dump` function cannot serialize NumPy types.
- **Parameters**:
    - `obj`: The Python object (potentially containing NumPy types) to convert.
- **Returns**: 
    - A new object with NumPy types converted to standard Python types.
- **Logic**: Uses `isinstance` checks to identify NumPy types and converts them. Recursively calls itself for dictionaries and lists.

### 3.3. `process_file(extractor, input_file_path, base_input_dir, base_output_dir)`

```python
def process_file(extractor, input_file_path, base_input_dir, base_output_dir):
    # ... (file processing logic)
```

- **Purpose**: Processes a single input text file: reads the content, uses the `IntegratedNERProcessor` instance to extract and group entities, and writes the results to the corresponding `.entities.json` and `.annotated.txt` files in the specified output directory, preserving the relative path structure.
- **Parameters**:
    - `extractor`: An instance of the `IntegratedNERProcessor` class.
    - `input_file_path` (str): The absolute path to the input `.txt` file.
    - `base_input_dir` (str): The base directory from which input files are being read (used to determine relative paths).
    - `base_output_dir` (str): The base directory where output files should be written.
- **Logic**:
    1. Prints the file being processed and records the start time.
    2. Determines the relative path of the input file with respect to `base_input_dir` using `os.path.relpath`.
    3. Constructs the output paths for the `.annotated.txt` and `.entities.json` files within `base_output_dir`, preserving the relative directory structure.
    4. Creates the necessary output directories using `os.makedirs(..., exist_ok=True)`.
    5. Reads the content of the `input_file_path`.
    6. Calls `extractor.extract_persons(text)` to get the `merged_entities` list and the `grouped_entity_dict`.
    7. **Writes JSON Output**: 
        - Converts the `grouped_entity_dict` using `convert_numpy_types` to ensure JSON serializability.
        - Opens the `json_output_path` and uses `json.dump` to write the dictionary with UTF-8 encoding, ensuring non-ASCII characters are preserved (`ensure_ascii=False`), and using indentation for readability (`indent=4`).
    8. **Writes Annotated Text Output**: 
        - Calls `annotate_text(text, merged_entities)` using the *merged* (but not grouped) entities.
        - Opens the `annotated_output_path` and writes the result with UTF-8 encoding.
    9. Calculates and prints the processing time, the number of unique persons found (keys in the grouped dict), and the total number of mentions (sum of list lengths in the grouped dict).

## 4. Main Execution Block (`main()` function)

```python
def main():
    # ... (main script logic)

if __name__ == "__main__":
    main()
```

- **Purpose**: This is the entry point of the script when executed from the command line. It handles argument parsing, finds the input files, initializes the extractor, and loops through the files calling `process_file` for each.
- **Logic**:
    1. **Argument Parsing**: Checks if exactly one command-line argument (`sys.argv[1]`) is provided. If not, prints a usage message and exits.
    2. **Input Path Handling**: 
        - Checks if the input path is a directory (`os.path.isdir`). If yes:
            - Sets `base_input_dir` to the absolute path of the directory.
            - Defines `base_output_dir` as a subdirectory within the parent directory of the input, named like `input_dir_name_output_grouped`.
            - Uses `glob.glob` with `recursive=True` to find all `.txt` files within the input directory and its subdirectories.
            - Filters the found paths to exclude any existing `.annotated.txt` or `.entities.json` files.
        - Checks if the input path is a single `.txt` file (`os.path.isfile` and `endswith(".txt")`). If yes:
            - Puts the single file path into the `file_paths` list.
            - Sets `base_input_dir` and `base_output_dir` to the directory containing the file.
        - If the input path is neither a directory nor a `.txt` file, prints an error and exits.
    3. **File Check**: Exits if no `.txt` files were found.
    4. **Dependency Check**: Includes a `try...except ImportError` block to check if `transformers` and `torch` are installed. Prints an error and exits if they are not found (though installation is handled externally in the current workflow).
    5. **Initialization**: Creates an instance of the `IntegratedNERProcessor` class.
    6. **Processing Loop**: 
        - Records the total start time.
        - Iterates through the `file_paths` list.
        - For each `file_path`, calls `process_file(extractor, file_path, base_input_dir, base_output_dir)`.
    7. **Completion Message**: Calculates and prints the total processing time and the average time per file.

- **`if __name__ == "__main__":`**: This standard Python construct ensures that the `main()` function is called only when the script is executed directly (not when imported as a module).


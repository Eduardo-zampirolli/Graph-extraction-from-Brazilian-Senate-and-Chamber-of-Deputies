# Named Entity Recognition (NER) Script - `ner.py`

## Overview

The `ner.py` script is a comprehensive tool for performing Named Entity Recognition (NER) on Portuguese text files, specifically targeting person entities ("PESSOA"). It combines rule-based methods with a pre-trained transformer model to extract, merge, deduplicate, and group similar person names.

## Features

1. **Entity Extraction**:
   - Uses a pre-trained transformer model (`pierreguillou/ner-bert-base-cased-pt-lenerbr`) for NER.
   - Includes rule-based methods for extracting parliamentary titles and names.

2. **Entity Merging**:
   - Merges adjacent or overlapping entities into a single entity.
   - Handles special cases like all-caps names.

3. **Deduplication**:
   - Removes duplicate entities with identical spans, keeping the highest-scoring one.

4. **Grouping**:
   - Groups similar person names under a canonical name using fuzzy string matching.

5. **Output Generation**:
   - Produces annotated text with `<PESSOA:Name>` tags.
   - Saves grouped entities as a JSON file.

## How It Works

1. **Text Processing**:
   - Cleans the input text and removes existing annotations.
   - Extracts entities using both rule-based and model-based methods.

2. **Entity Refinement**:
   - Merges adjacent entities.
   - Removes duplicates.
   - Filters for "PESSOA" entities.

3. **Grouping**:
   - Groups similar names under a canonical name using fuzzy matching.

4. **Output**:
   - Generates annotated text and grouped entity JSON files.

## Usage

### Command-Line Execution

Run the script with the following command:

```bash
python ner.py <input_directory_or_file_path>
```

- `<input_directory_or_file_path>`: Path to a directory or a `.txt` file containing the text to process.

### Outputs

- **Annotated Text**: `<input_file>.annotated.txt`
- **Grouped Entities**: `<input_file>.grouped_entities.json`

### Example

```bash
python ner.py /path/to/text/files
```

This will process all `.txt` files in the specified directory and save the results in an output directory.

## Requirements

Install the required libraries using:

```bash
pip install torch transformers fuzzywuzzy[speedup]
```

## Key Components

### 1. `IntegratedNERProcessor` Class

Encapsulates the logic for NER, merging, deduplication, and grouping.

- **`process_text`**: Orchestrates the entire NER process.
- **`_rule_based_ner`**: Extracts entities using predefined rules.
- **`_extract_entities_with_overlap`**: Handles long texts using a sliding window approach.
- **`_merge_adjacent_entities`**: Merges adjacent or overlapping entities.
- **`_remove_duplicate_spans`**: Removes duplicate entities.
- **`_group_similar_persons`**: Groups similar names under a canonical name.

### 2. Standalone Functions

- **`create_annotated_text`**: Generates annotated text with `<PESSOA:Name>` tags.
- **`save_grouped_entities`**: Saves grouped entities to a JSON file.
- **`save_annotated_text`**: Saves annotated text to a file.

## Notes

- The script is designed for Portuguese text and focuses on extracting person entities.
- It handles edge cases like overlapping entities and name variations.
- Modular and extensible for large-scale text processing tasks.

## Contact

For questions or issues, please contact the project maintainer.

import spacy
import pandas as pd

# Load text file
with open("senado/2024/26007.txt", "r", encoding="utf-8") as file:
    text = file.read()

# Load spaCy model
nlp = spacy.load("pt_core_news_lg")

# Process text
doc = nlp(text)

# Print all identified entities and their labels
for ent in doc.ents:
    print(f"Entity: {ent.text}, Label: {ent.label_}")

# Extract ONLY people (PERSON entities)
people = []
for ent in doc.ents:
    if ent.label_ == "PER" and len(ent.text.strip()) > 1:
        people.append({"name": ent.text.strip()})

# Remove duplicates
df_people = pd.DataFrame(people).drop_duplicates()

# Save to CSV
df_people.to_csv("people_list.csv", index=False)

print(f"Found {len(df_people)} people. Saved to 'people_list.csv'.")
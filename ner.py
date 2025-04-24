import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification, AdamW
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
import re

# 1. Custom Dataset Class
class ParliamentaryDataset(Dataset):
    def __init__(self, texts, tags, tokenizer, max_length=128):
        self.texts = texts
        self.tags = tags
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.label_map = {'O': 0, 'B-PER': 1, 'I-PER': 2}
        
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = self.texts[idx]
        word_tags = self.tags[idx]
        
        # Tokenize and align labels
        tokenized = self.tokenizer(
            text,
            truncation=True,
            is_split_into_words=True,
            max_length=self.max_length,
            padding='max_length'
        )
        
        labels = []
        word_ids = tokenized.word_ids()
        previous_word_idx = None
        
        for word_idx in word_ids:
            if word_idx is None:
                labels.append(-100)  # Special tokens
            elif word_idx != previous_word_idx:
                labels.append(self.label_map[word_tags[word_idx]])
            else:
                labels.append(self.label_map[word_tags[word_idx]] if word_tags[word_idx].startswith('I') else -100)
            previous_word_idx = word_idx
            
        return {
            'input_ids': torch.tensor(tokenized['input_ids']),
            'attention_mask': torch.tensor(tokenized['attention_mask']),
            'labels': torch.tensor(labels)
        }

# 2. Data Preparation (Example - adapt to your data)
def prepare_data(texts):
    all_texts = []
    all_tags = []
    
    for text in texts:
        # Split text into words
        words = re.findall(r'\w+|\S', text)
        tags = ['O'] * len(words)
        
        # Rule-based tagging for training data
        for i, word in enumerate(words):
            if word in ['SR.', 'SRA.', 'SR', 'SRA'] and i > 0 and words[i-1] in ['O', 'A']:
                # Mark names after titles
                j = i + 1
                while j < len(words) and words[j].isupper() and len(words[j]) > 1:
                    tags[j] = 'B-PER' if j == i+1 else 'I-PER'
                    j += 1
            elif word.startswith('(') and i > 0 and words[i-1].isupper():
                # Mark names in parentheses
                name_part = word.strip('()').split('.')[0]
                name_words = re.findall(r'\w+', name_part)
                for k, nw in enumerate(name_words):
                    if nw[0].isupper():
                        tags[i+k] = 'B-PER' if k == 0 else 'I-PER'
        
        all_texts.append(words)
        all_tags.append(tags)
    
    return all_texts, all_tags

# 3. Training Function
def train_model(texts, epochs=3, batch_size=8):
    # Prepare data
    tokenizer = AutoTokenizer.from_pretrained("neuralmind/bert-base-portuguese-cased")
    model = AutoModelForTokenClassification.from_pretrained(
        "neuralmind/bert-base-portuguese-cased",
        num_labels=3,
        id2label={0: 'O', 1: 'B-PER', 2: 'I-PER'},
        label2id={'O': 0, 'B-PER': 1, 'I-PER': 2}
    )
    
    # Prepare dataset
    texts, tags = prepare_data(texts)
    train_texts, val_texts, train_tags, val_tags = train_test_split(texts, tags, test_size=0.2)
    
    train_dataset = ParliamentaryDataset(train_texts, train_tags, tokenizer)
    val_dataset = ParliamentaryDataset(val_texts, val_tags, tokenizer)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size)
    
    # Training setup
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    optimizer = AdamW(model.parameters(), lr=5e-5)
    
    # Training loop
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        
        for batch in train_loader:
            optimizer.zero_grad()
            inputs = {k: v.to(device) for k, v in batch.items()}
            outputs = model(**inputs)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        # Validation
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for batch in val_loader:
                inputs = {k: v.to(device) for k, v in batch.items()}
                outputs = model(**inputs)
                val_loss += outputs.loss.item()
        
        print(f"Epoch {epoch+1}/{epochs}")
        print(f"Train Loss: {total_loss/len(train_loader):.4f}")
        print(f"Val Loss: {val_loss/len(val_loader):.4f}\n")
    
    return model, tokenizer

# 4. Example Usage
if __name__ == "__main__":
    # Example data (replace with your actual parliamentary transcripts)
    example_texts = [
        "O SR. PRESIDENTE (Rodrigo Pacheco. Bloco/DEM - MG) declarou a sessão aberta.",
        "A SRA. RELATORA (Maria Silva) apresentou seu parecer.",
        "O Deputado Federal João Oliveira discursou sobre o tema."
    ]
    
    # Train the model
    trained_model, tokenizer = train_model(example_texts, epochs=3)
    
    # Save the model
    trained_model.save_pretrained("./parliamentary_ner_model")
    tokenizer.save_pretrained("./parliamentary_ner_model")
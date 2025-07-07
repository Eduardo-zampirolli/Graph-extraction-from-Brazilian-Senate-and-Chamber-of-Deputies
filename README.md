# Graph Creation from Brazilian Senate and Chamber of Deputies

This repository contains a comprehensive pipeline to create network graphs from Brazilian parliamentary session transcripts. The project extracts text data from government websites, applies Named Entity Recognition (NER) to identify parliamentarians, and constructs interaction graphs based on speech patterns and mentions.

## About the Project

This project analyzes the dynamics of the Brazilian National Congress by creating network graphs from parliamentary session transcripts. Unlike traditional approaches that focus on legislative co-sponsorship, this method analyzes actual speech interactions and mentions between parliamentarians during sessions.

The pipeline consists of four main stages:
1. **Data Extraction**: Web scraping of session transcripts from official government websites
2. **Named Entity Recognition**: Identification of parliamentarian names using transformer-based models
3. **Graph Construction**: Creation of interaction networks based on speech patterns and mentions
4. **Analysis and Visualization**: Statistical analysis and visualization of the resulting networks

The project processes data from multiple sources:
- **Chamber of Deputies (Câmara)**: Session transcripts from 2016-2025
- **Federal Senate (Senado)**: Regular sessions from 2020-2024
- **Federal Senate (Senado R)**: Special sessions and committees from 2021-2025

## 🔧 Key Features

- **Web Scraping**: Automated extraction of session transcripts from official government websites
- **Named Entity Recognition**: Advanced NER using transformer models (BERT-based) to identify parliamentarian names
- **Entity Normalization**: Fuzzy matching and name standardization to handle variations in how names appear
- **Graph Construction**: Creation of weighted directed graphs where nodes are parliamentarians and edges represent interaction patterns
- **Statistical Analysis**: Comprehensive graph metrics including degree distribution, clustering coefficients, and network centrality measures
- **Visualization**: Multiple visualization options including static plots and interactive network displays

## 📂 Project Structure

The repository is organized as follows:

```
.
├── data_extraction/          # Scripts for web scraping and data collection
│   ├── achar_cod_*.py       # Code discovery scripts for finding session IDs
│   ├── *_txt.py             # Text extraction scripts from government websites
│   └── table.py             # Data aggregation and statistics
├── ner/                     # Named Entity Recognition pipeline
│   ├── ner.py               # Main NER processing script
│   ├── create_annotations.py # Annotation file creation
│   ├── compare_outputs.py   # Evaluation and comparison tools
│   └── README.md            # Detailed NER documentation
├── graph_creation/          # Graph construction and analysis
│   └── graph_joining.py     # Main graph creation script
├── resultados/              # Analysis and visualization scripts
│   ├── tabela.py            # Graph metrics calculation
│   ├── distrib*.py          # Degree distribution analysis
│   ├── analise_grafos.py    # Graph analysis tools
│   └── *.ipynb              # Jupyter notebooks for visualization
├── Camara/                  # Raw data from Chamber of Deputies
├── Senado/                  # Raw data from Federal Senate
├── testes/                  # Test files and validation data
└── requirements.txt         # Python dependencies
```

## 🚀 Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

- Python 3.8+ with pip installed
- At least 4GB of RAM (transformer models are memory-intensive)
- Internet connection for downloading pre-trained models

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/Graph-creation-with-html.git
   cd Graph-creation-with-html
   ```

2. **Install dependencies:**
   It is recommended to use a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
   Then install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ Usage

The pipeline consists of multiple stages that can be run independently or in sequence:

### 1. Data Extraction

First, discover session codes and extract text data:

```bash
# Find session codes for Chamber of Deputies
python data_extraction/achar_cod_cam.py

# Extract text from Chamber sessions
python data_extraction/cam_txt.py

# Find session codes for Senate
python data_extraction/achar_cod_sen_s.py
python data_extraction/achar_cod_sen_r.py

# Extract text from Senate sessions
python data_extraction/sen_txt.py
python data_extraction/sen_r.py
```

### 2. Named Entity Recognition

Process the extracted texts to identify parliamentarians:

```bash
# Run NER on extracted texts
python ner/ner.py <input_directory> <output_directory>

# Create annotated files
python ner/create_annotations.py --original-dir <text_dir> --json-dir <json_dir> --output-dir <output_dir>
```

### 3. Graph Construction

Build interaction graphs from the annotated texts:

```bash
# Create graphs from annotated texts
python graph_creation/graph_joining.py <input_directory> <output_directory>
```

### 4. Analysis and Visualization

Analyze the generated graphs:

```bash
# Calculate graph metrics
python resultados/tabela.py <graphs_directory>

# Generate degree distribution plots
python resultados/distrib.py <graphs_directory>

# Open Jupyter notebooks for interactive analysis
jupyter notebook resultados/Plots.ipynb #for data plot
jupyter notebook resultados/graph_plot.ipynb #for graph visualization
```

## 📊 Results and Output

The pipeline generates several types of outputs:

### Data Files
- **Raw Text Files**: Extracted session transcripts organized by year and institution
- **JSON Files**: NER results with identified entities and their positions
- **Annotated Files**: Text files with embedded entity tags for validation

### Graph Files
- **GEXF Format**: Network graphs compatible with Gephi and other network analysis tools
- **Graph Metrics**: CSV files containing network statistics (degree, clustering, centrality measures)

### Visualizations
- **Degree Distribution Plots**: Analysis of network connectivity patterns
- **Interactive Notebooks**: Jupyter notebooks for exploring the data
- **Network Visualizations**: Static and interactive graph plots

### Key Metrics Calculated
- **Network Structure**: Number of nodes, edges, density, diameter
- **Centrality Measures**: Degree, betweenness, closeness centrality
- **Clustering**: Local and global clustering coefficients
- **Degree Distribution**: Power-law fitting and statistical analysis

## 🔬 Technical Details

### Named Entity Recognition
- Uses transformer-based models (BERT) fine-tuned for Portuguese
- Implements fuzzy matching for name normalization
- Handles parliamentary titles and formal address patterns
- Evaluation framework with precision, recall, and F1-score metrics

### Graph Construction
- Weighted directed graphs based on mention frequency
- Speaker-mention relationships from session transcripts
- Name disambiguation using fuzzy string matching
- Temporal analysis capabilities (graphs by year)

### Data Sources
- **Chamber of Deputies**: `https://escriba.camara.leg.br/escriba-servicosweb/html/{code}`
- **Federal Senate**: `https://www25.senado.leg.br/web/atividade/notas-taquigraficas/-/notas/s/{code}`
- **Senate Committees**: `https://www25.senado.leg.br/web/atividade/notas-taquigraficas/-/notas/r/{code}`

## 🧪 Testing and Validation

The repository includes comprehensive testing infrastructure:

- **Manual Annotation**: Ground truth files for NER evaluation
- **Comparison Tools**: Automated evaluation of NER performance
- **Test Cases**: Sample files for validating the pipeline
- **Error Analysis**: Tools for identifying and analyzing processing errors

## 📈 Performance Considerations

- **Memory Usage**: Transformer models require significant RAM (4GB+ recommended)
- **Processing Time**: NER processing can be time-intensive for large datasets
- **Storage**: Raw data and results can occupy several GB of disk space
- **GPU Support**: CUDA-enabled GPUs will significantly speed up NER processing


## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Brazilian government for providing open access to parliamentary data
- Hugging Face for transformer models and tools
- NetworkX and igraph communities for graph analysis libraries
- The open-source community for the various tools and libraries used

## 📬 Contact

For questions about this project, please open an issue in the repository or contact the maintainers.

---

*This project is part of research into Brazilian parliamentary dynamics and network analysis. The data used is publicly available from official government sources.*



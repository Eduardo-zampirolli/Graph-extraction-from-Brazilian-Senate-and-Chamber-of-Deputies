# Results and Analysis - Resultados

This directory contains all the analysis scripts, visualization tools, and output files for processing the parliamentary interaction graphs. The scripts in this folder provide comprehensive statistical analysis and visualization capabilities for the network graphs generated from Brazilian parliamentary session transcripts.

## 📊 Overview

The `resultados/` directory serves as the analytical hub of the project, containing tools to:
- Calculate comprehensive graph metrics and statistics
- Generate degree distribution analyses
- Create visualizations of network structures
- Perform comparative analysis across different years and institutions
- Export results in various formats (CSV, PNG, interactive notebooks)

## 📁 Files Description

### 🔢 Statistical Analysis Scripts

#### `tabela.py`
**Purpose**: Comprehensive graph metrics calculation
**Usage**: `python tabela.py <graphs_directory>`
**Output**: CSV files with network statistics

**Metrics Calculated**:
- **Vertices**: Number of nodes (parliamentarians)
- **Edges**: Number of connections
- **Average Degree**: Mean connectivity per node
- **Clustering Coefficient**: Local clustering measure (weighted)
- **Average Distance**: Mean shortest path length (weighted)
- **Density**: Network connectivity density
- **Diameter**: Maximum shortest path length (weighted)

**Output Files**:
- `camara_metrics_YYYYMMDD_HHMMSS.csv`
- `senado_metrics_YYYYMMDD_HHMMSS.csv`
- `senado_r_metrics_YYYYMMDD_HHMMSS.csv`

#### `distrib.py`
**Purpose**: Degree distribution analysis with power-law fitting
**Usage**: `python distrib.py <graphs_directory>`
**Output**: Distribution plots with statistical fits

**Features**:
- Log-log degree distribution plots
- Power-law fitting with R² correlation
- Comparative analysis across years
- Separate plots for each institution type

#### `distr_cumul.py`
**Purpose**: Cumulative degree distribution analysis
**Usage**: `python distr_cumul.py <graphs_directory>`
**Output**: Complementary Cumulative Distribution Function (CCDF) plots

**Features**:
- CCDF analysis for degree distributions
- Comparison across different years
- Statistical significance testing

#### `distr_cumul_norm.py`
**Purpose**: Normalized cumulative distribution analysis
**Usage**: `python distr_cumul_norm.py <graphs_directory>`
**Output**: Normalized CCDF plots with power-law fitting

**Features**:
- Normalized distribution analysis
- Advanced power-law fitting
- Statistical validation of scale-free properties

#### `distr_norm.py`
**Purpose**: Normalized degree distribution analysis
**Usage**: `python distr_norm.py <graphs_directory>`
**Output**: Normalized distribution plots

**Features**:
- Probability density function analysis
- Normalization across different graph sizes
- Statistical curve fitting

### 📓 Interactive Notebooks

#### `Plots.ipynb`
**Purpose**: Interactive data visualization and analysis
**Content**:
- Parliamentary data overview by year
- Session type distribution analysis
- Statistical summaries and trend analysis
- Custom plotting functions

**Key Visualizations**:
- Bar charts of session counts by year and type
- Comparative analysis between institutions
- Temporal trend analysis

#### `graph_plot.ipynb`
**Purpose**: Interactive graph visualization
**Content**:
- Network graph plotting with customizable parameters
- Node sizing based on degree centrality
- Color coding for different node properties
- Interactive parameter adjustment

### 📈 Data Files

#### `est-dir - parliament_data_by_year.csv`
**Description**: Aggregated parliamentary session statistics
**Content**:
- Session counts by year and institution
- Session type breakdown
- Temporal distribution analysis

**Columns**:
- `Ano`: Year
- `Fonte`: Source institution (Camara, Senado, etc.)
- `Tipo`: Session type
- `Count`: Number of sessions

#### `dados_por_ano.png`
**Description**: Static visualization of parliamentary data distribution by year

#### `Tabela_tipo_ano.png`
**Description**: Table visualization showing session types and counts by year

## 🚀 Usage Examples

### Basic Graph Metrics Calculation
```bash
# Calculate metrics for all graphs
python tabela.py /path/to/graphs

# This will create CSV files in the graphs/metrics/ directory
```

### Degree Distribution Analysis
```bash
# Generate degree distribution plots
python distrib.py /path/to/graphs

# Output: graphs/distribution/ directory with plots
```

### Cumulative Distribution Analysis
```bash
# Generate CCDF plots
python distr_cumul.py /path/to/graphs

# Output: graphs/cumulative_distribution/ directory
```

### Interactive Visualization
```bash
# Start Jupyter notebook for interactive analysis
jupyter notebook Plots.ipynb

# Or for graph plotting
jupyter notebook graph_plot.ipynb
```

### Custom Graph Visualization
Graph visualization can be performed using the Jupyter notebooks or by using standard Python libraries:

```python
import igraph as ig
import matplotlib.pyplot as plt
import networkx as nx

# Load and plot a graph
file_path = "path/to/graph.gexf"
nwx_graph = nx.read_gexf(file_path)
ig_graph = ig.Graph.from_networkx(nwx_graph)

# Create a simple plot
layout = ig_graph.layout("fr")  # Fruchterman-Reingold layout
ig.plot(ig_graph, layout=layout, bbox=(800, 600), margin=20)
```

## 📋 Output Structure

When running the analysis scripts, the following directory structure is created:

```
graphs/
├── metrics/
│   ├── camara_metrics_YYYYMMDD_HHMMSS.csv
│   ├── senado_metrics_YYYYMMDD_HHMMSS.csv
│   └── senado_r_metrics_YYYYMMDD_HHMMSS.csv
├── distribution/
│   ├── camara/
│   │   ├── degree_distribution_combined.png
│   │   └── individual_year_plots.png
│   ├── senado/
│   └── senado_r/
├── cumulative_distribution/
│   ├── camara/
│   ├── senado/
│   └── senado_r/
└── plots/
    ├── high_resolution_graphs/
    └── interactive_outputs/
```

## 📊 Metrics Interpretation

### Network Metrics
- **High Clustering Coefficient**: Indicates strong local connectivity (political groups)
- **Low Average Distance**: Suggests efficient information flow
- **High Density**: Indicates well-connected network
- **Power-law Degree Distribution**: Suggests scale-free network properties

### Degree Distribution Analysis
- **Power-law Exponent**: Indicates scale-free properties
- **R² Value**: Goodness of fit for power-law model
- **Heavy Tail**: Presence of highly connected nodes (influential parliamentarians)

## 🔧 Technical Requirements

### Dependencies
- `igraph`: Graph analysis and visualization
- `networkx`: Alternative graph processing
- `matplotlib`: Plotting and visualization
- `numpy`: Numerical computations
- `scipy`: Scientific computing
- `pandas`: Data manipulation (for notebooks)
- `seaborn`: Statistical visualization (for notebooks)

### Performance Considerations
- **Memory Usage**: Large graphs (>10,000 nodes) require significant RAM
- **Processing Time**: Metric calculations scale with graph size
- **Visualization**: Large graphs may require layout optimization
- **Storage**: High-resolution plots can be several MB each


## 🔍 Troubleshooting

### Common Issues
- **Memory errors**: Reduce graph size or increase available RAM
- **Slow processing**: Use faster layout algorithms or reduce visualization complexity
- **Missing dependencies**: Ensure all required packages are installed
- **File format errors**: Verify GEXF files are properly formatted

## 📚 Further Reading

For detailed information about specific analysis methods:
- Graph theory metrics: [NetworkX Documentation](https://networkx.org/documentation/stable/)
- Network visualization: [igraph Documentation](https://igraph.org/python/)
- Statistical analysis: [SciPy Documentation](https://scipy.org/)

---

*This analysis suite provides comprehensive tools for understanding Brazilian parliamentary interaction networks through quantitative graph analysis and visualization.*

import igraph as ig
import numpy as np
import networkx as nx
import sys, os, glob
import matplotlib.pyplot as plt

def calculate_cumulative_distribution(values):
    """Calculate the complementary cumulative distribution function (CCDF)"""
    unique_values, counts = np.unique(values, return_counts=True)
    total = len(values)
    
    # Calculate probability P(X >= x)
    probs = np.cumsum(counts[::-1])[::-1] / total
    
    return unique_values, probs

def plot_distribution(file_list, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    
    for filename in file_list:
        try:
            year = os.path.basename(filename).split('_')[1].split('.')[0]
            nwx = nx.read_gexf(filename)
            
            # Convert to unweighted graph by ignoring weights
            unweighted_nwx = nx.Graph()
            unweighted_nwx.add_nodes_from(nwx.nodes())
            unweighted_nwx.add_edges_from(nwx.edges())
            
            graph = ig.Graph.from_networkx(unweighted_nwx)
            
            # Degree distribution (instead of strength distribution)
            degrees = graph.degree()
            unique_degrees, cum_probs = calculate_cumulative_distribution(degrees)
            
            plt.figure(figsize=(10, 6))
            plt.loglog(unique_degrees, cum_probs, 'bo', markersize=5)
            plt.title(f"Distribuição acumulativa de grau em {year} (Log-Log)")
            plt.xlabel("Grau (log)")
            plt.ylabel("Probabilidade acumulativa P(X ≥ x) (log)")
            plt.grid(True, which="both", linestyle='--')
            plt.savefig(os.path.join(out_dir, f"degree_{year}.png"))
            plt.close()
            
            # In-degree distribution
            in_degrees = graph.degree(mode='in')
            in_unique_degrees, in_cum_probs = calculate_cumulative_distribution(in_degrees)
            
            plt.figure(figsize=(10, 6))
            plt.loglog(in_unique_degrees, in_cum_probs, 'go', markersize=5)
            plt.title(f"Distribuição acumulativa de grau de entrada em {year} (Log-Log)")
            plt.xlabel("Grau de entrada (log)")
            plt.ylabel("Probabilidade acumulativa P(X ≥ x) (log)")
            plt.grid(True, which="both", linestyle='--')
            plt.savefig(os.path.join(out_dir, f"in_degree_{year}.png"))
            plt.close()
            
            # Out-degree distribution
            out_degrees = graph.degree(mode='out')
            out_unique_degrees, out_cum_probs = calculate_cumulative_distribution(out_degrees)
            
            plt.figure(figsize=(10, 6))
            plt.loglog(out_unique_degrees, out_cum_probs, 'ro', markersize=5)
            plt.title(f"Distribuição acumulativa de grau de saída em {year} (Log-Log)")
            plt.xlabel("Grau de saída (log)")
            plt.ylabel("Probabilidade acumulativa P(X ≥ x) (log)")
            plt.grid(True, which="both", linestyle='--')
            plt.savefig(os.path.join(out_dir, f"out_degree_{year}.png"))
            plt.close()
            
            print(f"Processed {year}")
            
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python graph_metrics.py path/to/graphs")
        return
    
    input_dir = sys.argv[1]
    
    if not os.path.isdir(input_dir):
        print(f"Error: Input directory not found: {input_dir}")
        return
    
    output_dir = os.path.join(input_dir, "degree_distribution")  # Changed directory name
    os.makedirs(output_dir, exist_ok=True)
    
    list_cam = sorted(glob.glob(os.path.join(input_dir, "camara", "*.gexf")))
    list_sen = sorted(glob.glob(os.path.join(input_dir, "senado", "*.gexf")))
    list_senr = sorted(glob.glob(os.path.join(input_dir, "senado_r", "*.gexf")))
    
    plot_distribution(list_cam, os.path.join(output_dir, "camara"))
    plot_distribution(list_sen, os.path.join(output_dir, "senado"))
    plot_distribution(list_senr, os.path.join(output_dir, "senado_r"))
    
    print(f"Processing completed. Plots saved in: {output_dir}")

if __name__ == "__main__":
    main()
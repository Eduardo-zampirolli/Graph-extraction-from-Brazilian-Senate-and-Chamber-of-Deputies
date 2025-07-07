import igraph as ig
import numpy as np
import networkx as nx
import sys, os, glob
import matplotlib.pyplot as plt

def power_law(x, a, b):
    return a * np.power(x, b)

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
            graph = ig.Graph.from_networkx(nwx) # igraph graph, should preserve weights
            
            # Total strength distribution
            strengths = graph.strength(weights='weight')
            unique_strengths, cum_probs = calculate_cumulative_distribution(strengths)
            
            plt.figure(figsize=(10, 6))
            plt.loglog(unique_strengths, cum_probs, 'bo', markersize=5)
            plt.title(f"Distribuição acumulativa de força total em {year} (Log-Log)")
            plt.xlabel("Força (log)")
            plt.ylabel("Probabilidade acumulativa P(X ≥ x) (log)")
            plt.grid(True, which="both", linestyle='--')
            plt.savefig(os.path.join(out_dir, f"total_{year}.png"))
            plt.close()
            
            # In-strength distribution
            instrengths = graph.strength(mode='in', weights='weight')
            inunique_strengths, incum_probs = calculate_cumulative_distribution(instrengths)
            
            plt.figure(figsize=(10, 6))
            plt.loglog(inunique_strengths, incum_probs, 'go', markersize=5)
            plt.title(f"Distribuição acumulativa de força de entrada em {year} (Log-Log)")
            plt.xlabel("Força entrada (log)")
            plt.ylabel("Probabilidade acumulativa P(X ≥ x) (log)")
            plt.grid(True, which="both", linestyle='--')
            plt.savefig(os.path.join(out_dir, f"in_{year}.png"))
            plt.close()
            
            # Out-strength distribution
            outstrengths = graph.strength(mode='out', weights='weight')
            outunique_strengths, outcum_probs = calculate_cumulative_distribution(outstrengths)
            
            plt.figure(figsize=(10, 6))
            plt.loglog(outunique_strengths, outcum_probs, 'ro', markersize=5)
            plt.title(f"Distribuição acumulativa de força de saída em {year} (Log-Log)")
            plt.xlabel("Força saída (log)")
            plt.ylabel("Probabilidade acumulativa P(X ≥ x) (log)")
            plt.grid(True, which="both", linestyle='--')
            plt.savefig(os.path.join(out_dir, f"out_{year}.png"))
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
    
    output_dir = os.path.join(input_dir, "cumulative_distribution")  # Changed directory name
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
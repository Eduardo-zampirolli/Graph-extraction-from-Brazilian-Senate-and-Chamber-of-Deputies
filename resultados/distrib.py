import igraph as ig
import numpy as np
import networkx as nx
import sys, os, glob
import matplotlib.pyplot as plt

def add_linear_fit(degrees, counts, color='r', label_prefix=""):
    """Improved linear fit for power law distributions"""
    # Filter zeros and get log values
    mask = (counts > 0) & (degrees > 0)
    log_deg = np.log10(degrees[mask])
    log_cnt = np.log10(counts[mask])
    
    if len(log_deg) < 3:  # Need at least 3 points for fit
        return None, None, None
    
    # Focus on the tail (ignore first 10% of points)
    cutoff = int(0.1 * len(log_deg))
    log_deg_tail = log_deg[:cutoff]
    log_cnt_tail = log_cnt[:cutoff]
    
    # Robust linear regression
    slope, intercept = np.polyfit(log_deg_tail, log_cnt_tail, 1)
    r_squared = np.corrcoef(log_deg_tail, log_cnt_tail)[0,1]**2
    
    # Plot fitted line
    fit_counts = 10**(intercept + slope*log_deg_tail)
    plt.plot(10**log_deg_tail, fit_counts, color=color, linestyle='--',
            label=f'{label_prefix}Fit: y={10**intercept:.2f}x^{slope:.2f}\nR²={r_squared:.2f}')
    
    return slope, intercept, r_squared

def plot_distribution(file_list, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    
    for filename in file_list:
        try:
            year = os.path.basename(filename).split('_')[1].split('.')[0]
            nwx = nx.read_gexf(filename)
            graph = ig.Graph.from_networkx(nwx)
            
            # Total degrees
            degrees = graph.degree()
            unique_degrees, counts = np.unique(degrees, return_counts=True)
            
            plt.figure(figsize=(10, 6))
            plt.loglog(unique_degrees, counts, 'bo', markersize=5, label='Data')
            add_linear_fit(unique_degrees, counts, 'r', "Total ")
            plt.title(f"Distribuição de graus em {year} (Log-Log)")
            plt.xlabel("Grau (log)")
            plt.ylabel("Quantidade (log)")
            plt.grid(True, which="both", linestyle='--')
            plt.legend()
            plt.savefig(os.path.join(out_dir, f"total_{year}.png"))
            plt.close()
            
            # In-degrees
            indegrees = graph.indegree()
            inunique_degrees, incounts = np.unique(indegrees, return_counts=True)
            
            plt.figure(figsize=(10, 6))
            plt.loglog(inunique_degrees, incounts, 'go', markersize=5, label='In-degree Data')
            add_linear_fit(inunique_degrees, incounts, 'm', "In-degree ")
            plt.title(f"Distribuição de graus entrada em {year} (Log-Log)")
            plt.xlabel("Grau entrada (log)")
            plt.ylabel("Quantidade (log)")
            plt.grid(True, which="both", linestyle='--')
            plt.legend()
            plt.savefig(os.path.join(out_dir, f"in_{year}.png"))
            plt.close()
            
            # Out-degrees
            outdegrees = graph.outdegree()
            outunique_degrees, outcounts = np.unique(outdegrees, return_counts=True)
            
            plt.figure(figsize=(10, 6))
            plt.loglog(outunique_degrees, outcounts, 'ro', markersize=5, label='Out-degree Data')
            add_linear_fit(outunique_degrees, outcounts, 'c', "Out-degree ")
            plt.title(f"Distribuição de graus saída em {year} (Log-Log)")
            plt.xlabel("Grau saída (log)")
            plt.ylabel("Quantidade (log)")
            plt.grid(True, which="both", linestyle='--')
            plt.legend()
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
    
    output_dir = os.path.join(input_dir, "distribution")
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
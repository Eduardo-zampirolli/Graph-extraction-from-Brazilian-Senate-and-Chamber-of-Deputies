import igraph as ig
import numpy as np
import networkx as nx
import sys, os, glob
import matplotlib.pyplot as plt
from scipy import optimize

def power_law(x, a, b):
    return a * np.power(x, b)

def add_power_law_fit(degrees, probs, color='r', label_prefix=""):
    """Improved power law fit using nonlinear least squares"""
    # Filter zeros and get log values
    mask = (probs > 0) & (degrees > 0)
    x_data = degrees[mask]
    y_data = probs[mask]
    
    if len(x_data) < 3:  # Need at least 3 points for fit
        return None, None, None
    
    try:
        # Initial guess for parameters
        params, _ = optimize.curve_fit(power_law, x_data, y_data, 
                                      p0=[1, -2], maxfev=5000)
        
        # Calculate R-squared
        residuals = y_data - power_law(x_data, *params)
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y_data - np.mean(y_data))**2)
        r_squared = 1 - (ss_res / ss_tot)
        
        # Plot fitted line
        x_fit = np.logspace(np.log10(min(x_data)), np.log10(max(x_data)), 100)
        y_fit = power_law(x_fit, *params)
        plt.plot(x_fit, y_fit, color=color, linestyle='--',
                label=f'{label_prefix}Fit: y={params[0]:.2f}x^{params[1]:.2f}\nR²={r_squared:.2f}'
        )
        
        return params[1], params[0], r_squared  # slope, intercept, r_squared
    
    except Exception as e:
        print(f"Fit failed: {str(e)}")
        return None, None, None

def plot_distribution(file_list, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    
    for filename in file_list:
        try:
            year = os.path.basename(filename).split('_')[1].split('.')[0]
            nwx = nx.read_gexf(filename)
            graph = ig.Graph.from_networkx(nwx) # igraph graph, should preserve weights
            N = graph.vcount()  # Total number of nodes
            
            # Total strength distribution
            strengths = graph.strength(weights='weight')
            unique_strengths, counts = np.unique(strengths, return_counts=True)
            probs = counts / N  # Normalized probability
            
            plt.figure(figsize=(10, 6))
            plt.loglog(unique_strengths, probs, 'bo', markersize=5, label='Data')
            add_power_law_fit(unique_strengths, probs, 'r', "Total")
            plt.title(f"Distribuição normalizada de força total em {year} (Log-Log)")
            plt.xlabel("Força (log)")
            plt.ylabel("Probabilidade (log)")
            plt.grid(True, which="both", linestyle='--')
            plt.legend()
            plt.savefig(os.path.join(out_dir, f"total_{year}.png"))
            plt.close()
            
            # In-strength distribution
            instrengths = graph.strength(mode='in', weights='weight')
            inunique_strengths, incounts = np.unique(instrengths, return_counts=True)
            inprobs = incounts / N
            
            plt.figure(figsize=(10, 6))
            plt.loglog(inunique_strengths, inprobs, 'go', markersize=5, label='In-strength Data')
            add_power_law_fit(inunique_strengths, inprobs, 'm', "Entrada")
            plt.title(f"Distribuição normalizada de força de entrada em {year} (Log-Log)")
            plt.xlabel("Força entrada (log)")
            plt.ylabel("Probabilidade (log)")
            plt.grid(True, which="both", linestyle='--')
            plt.legend()
            plt.savefig(os.path.join(out_dir, f"in_{year}.png"))
            plt.close()
            
            # Out-strength distribution
            outstrengths = graph.strength(mode='out', weights='weight')
            outunique_strengths, outcounts = np.unique(outstrengths, return_counts=True)
            outprobs = outcounts / N
            
            plt.figure(figsize=(10, 6))
            plt.loglog(outunique_strengths, outprobs, 'ro', markersize=5, label='Out-strength Data')
            add_power_law_fit(outunique_strengths, outprobs, 'c', "Saida ")
            plt.title(f"Distribuição normalizada de força de saída em {year} (Log-Log)")
            plt.xlabel("Força saída (log)")
            plt.ylabel("Probabilidade (log)")
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
    
    output_dir = os.path.join(input_dir, "normalized_distribution")
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


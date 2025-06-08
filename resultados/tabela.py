import igraph as ig
import networkx as nx
import sys, os, glob
import csv
from datetime import datetime

def calculate_graph_metrics(graph):
    """Calculate all required metrics for a graph"""
    metrics = {
        'vertices': graph.vcount(),
        'edges': graph.ecount(),
        'average_degree': sum(graph.degree()) / graph.vcount(),
        'clustering_coef': graph.transitivity_undirected(),
        'avg_distance': graph.average_path_length(directed=False),
        'density': graph.density(),
        'diameter': graph.diameter(directed=False)
    }
    return metrics

def process_graph_files(file_list, output_csv):
    """Process a list of graph files and write metrics to CSV"""
    with open(output_csv, 'w', newline='') as csvfile:
        fieldnames = ['year', 'vertices', 'edges', 'average_degree', 
                     'clustering_coef', 'avg_distance', 'density', 'diameter']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for filename in file_list:
            try:
                # Extract year from filename (assuming format like grafo_YYYY.gexf)
                year = os.path.basename(filename).split('_')[1].split('.')[0]
                
                # Read and convert graph
                nwx = nx.read_gexf(filename)
                graph = ig.Graph.from_networkx(nwx)
                
                # Calculate metrics
                metrics = calculate_graph_metrics(graph)
                metrics['year'] = year
                
                writer.writerow(metrics)
                print(f"Processed {filename}")
                
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
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join(input_dir, "metrics")
    os.makedirs(output_dir, exist_ok=True)
    
    # Get sorted file lists
    list_cam = sorted(glob.glob(os.path.join(input_dir, "camara", "*.gexf")))
    list_sen = sorted(glob.glob(os.path.join(input_dir, "senado", "*.gexf")))
    list_senr = sorted(glob.glob(os.path.join(input_dir, "senado_r", "*.gexf")))
    
    # Process each list and save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    process_graph_files(list_cam, os.path.join(output_dir, f"camara_metrics_{timestamp}.csv"))
    process_graph_files(list_sen, os.path.join(output_dir, f"senado_metrics_{timestamp}.csv"))
    process_graph_files(list_senr, os.path.join(output_dir, f"senado_r_metrics_{timestamp}.csv"))
    
    print("Processing completed. CSV files saved in:", output_dir)

if __name__ == "__main__":
    main()
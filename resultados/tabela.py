import igraph as ig
import networkx as nx
import sys, os, glob
import csv
from datetime import datetime

def calculate_graph_metrics(nwx_graph, ig_graph):
    """Calculate all required metrics for a graph, considering directionality and weights"""
    metrics = {
        'vertices': ig_graph.vcount(),
        'edges': ig_graph.ecount(),
        'average_degree': sum(ig_graph.degree(mode="all")) / ig_graph.vcount(),
        'density': ig_graph.density(),
    }
    
    # Handle directed/undirected cases appropriately
    is_directed = ig_graph.is_directed()
    
    # Clustering coefficient - use appropriate method based on graph type
    if is_directed:
        # For directed graphs, we'll use igraph's implementation
        try:
            metrics['clustering_coef'] = ig_graph.transitivity_avglocal()
        except AttributeError:
            # Fallback if transitivity_avglocal not available
            clustering_local = ig_graph.transitivity_local_undirected()
            metrics['clustering_coef'] = sum(clustering_local) / len(clustering_local)
    else:
        metrics['clustering_coef'] = ig_graph.transitivity_undirected()
    
    # Path-based metrics (handle weights appropriately)
    weights = "weight" if "weight" in ig_graph.edge_attributes() else None
    
    try:
        metrics['avg_distance'] = ig_graph.average_path_length(directed=is_directed, 
                                                             weights=weights)
        metrics['diameter'] = ig_graph.diameter(directed=is_directed, 
                                               weights=weights)
    except (ig.InternalError, TypeError):
        # Fallback for disconnected graphs or other issues
        metrics['avg_distance'] = float('nan')
        metrics['diameter'] = float('nan')
    
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
                year = os.path.basename(filename).split('_')[1].split('.')[0]
                
                # Read with networkx first to preserve all attributes
                nwx = nx.read_gexf(filename)
                
                # Convert to igraph, preserving directionality and weights
                graph = ig.Graph.from_networkx(nwx)
                
                # Transfer weights if they exist
                if 'weight' in nwx.edges[list(nwx.edges)[0]]:
                    graph.es['weight'] = [e[2]['weight'] for e in nwx.edges(data=True)]
                
                metrics = calculate_graph_metrics(nwx, graph)
                metrics['year'] = year
                
                writer.writerow(metrics)
                print(f"Processed {filename}")
                
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

# ... rest of your main() function remains the same ...
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


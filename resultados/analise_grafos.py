import igraph as ig
import matplotlib.pyplot as plt
import networkx as nx # For fallback GEXF reading

def plot_gexf_graph(file_path, layout_algorithm='drl', show_labels=True, node_size=15, 
                    edge_width=1, figure_size=(120, 120), output_filename=None, dpi=100): # Added dpi
    """
    Reads a GEXF file, plots the graph using igraph, and displays or saves it.

    Args:
        file_path (str): The path to the .gexf file.
        layout_algorithm (str): Layout algorithm. 'fr' or 'drl' are often better for large graphs.
        show_labels (bool): Whether to display node labels. Strongly recommend False for large graphs.
        node_size (int): Size of nodes.
        edge_width (float): Width of edges.
        figure_size (tuple): Size of the matplotlib figure in inches (for interactive display).
        output_filename (str, optional): If provided, saves the plot to this file instead of showing it.
                                         Example: "graph_plot.png" or "graph_plot.svg".
        dpi (int): Dots per inch for the saved image.
    """
    try:
        graph = None
        print(f"Attempting to load graph from {file_path} using igraph.read()...")
        try:
            graph = ig.read(file_path, format="gexf")
            print("Successfully loaded graph using igraph.read().")
        except Exception as e_igraph:
            print(f"igraph.read() failed: {e_igraph}")
            print("Falling back to NetworkX for GEXF reading...")
            try:
                nwx = nx.read_gexf(file_path)
                graph = ig.Graph.from_networkx(nwx)
                print("Successfully loaded graph using NetworkX and converted to igraph.")
            except Exception as e_nx:
                print(f"NetworkX reading also failed: {e_nx}")
                raise 

        if not graph:
            print("Graph could not be loaded.")
            return

        print(f"Number of vertices: {graph.vcount()}")
        print(f"Number of edges: {graph.ecount()}")

        if graph.vcount() == 0:
            print("Graph is empty. Nothing to plot.")
            return

        print(f"Preparing plot with layout: {layout_algorithm}, show_labels: {show_labels}, node_size: {node_size}")

        layout = graph.layout(layout_algorithm)

        visual_style = {}
        visual_style["layout"] = layout
        visual_style["vertex_size"] = node_size
        
        if 'color' in graph.vs.attributes() and any(graph.vs['color']):
            visual_style["vertex_color"] = graph.vs["color"]
        else:
            visual_style["vertex_color"] = "skyblue"

        visual_style["edge_width"] = edge_width
        if 'color' in graph.es.attributes() and any(graph.es['color']):
            visual_style["edge_color"] = graph.es["color"]
        else:
            visual_style["edge_color"] = "grey"

        if show_labels:
            print("Warning: Plotting labels for a large graph can be very slow and memory intensive.")
            if "label" in graph.vs.attributes() and any(graph.vs["label"]):
                visual_style["vertex_label"] = graph.vs["label"]
            elif "id" in graph.vs.attributes() and any(graph.vs["id"]):
                visual_style["vertex_label"] = graph.vs["id"]
            else:
                visual_style["vertex_label"] = [str(i) for i in range(graph.vcount())]
            visual_style["vertex_label_size"] = max(6, int(figure_size[0] * 0.4)) # Adjusted label size
            visual_style["vertex_label_dist"] = 1.0 
            visual_style["vertex_label_color"] = "black"
        else:
            visual_style["vertex_label"] = None

        # 3. Plot the graph
        print("Plotting graph...")
        
        if output_filename:
            print(f"Saving plot to {output_filename}...")
            # For saving directly, bbox defines the image dimensions in pixels.
            # Let's make it reasonably large based on figure_size and dpi.
            # We can also remove margin to let the graph use the full bbox.
            visual_style["bbox"] = (figure_size[0] * dpi, figure_size[1] * dpi)
            visual_style["margin"] = 20 # Small margin to avoid cutting off nodes at the edge
            ig.plot(graph, output_filename, **visual_style)
            print(f"Plot saved to {output_filename}")
        else:
            # Interactive plotting with Matplotlib
            # For interactive, don't set bbox in visual_style, let matplotlib handle it.
            # visual_style.pop("bbox", None) # Ensure bbox is not used for interactive
            # visual_style.pop("margin", None) # Ensure margin is not used for interactive

            fig, ax = plt.subplots(figsize=figure_size, dpi=dpi)
            ig.plot(graph, target=ax, **visual_style) # Pass visual_style without bbox/margin for interactive
            ax.set_title(f"Graph from {file_path.split('/')[-1]} (Layout: {layout_algorithm})")
            plt.axis('off') 
            plt.tight_layout() 
            plt.show()
            print("Plot displayed.")

    except MemoryError:
        print("MemoryError: The process ran out of memory while trying to plot the graph.")
        print("Suggestions for large graphs:")
        print("- Set show_labels=False (labels are very memory intensive).")
        print("- Use a smaller node_size.")
        print("- Try a different layout_algorithm (e.g., 'fr', 'drl', or 'auto').")
        print("- Plot directly to a file (e.g., output_filename='graph.png') instead of interactive display.")
        print("- If possible, run on a machine with more RAM.")
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please ensure the GEXF file is valid and igraph/pycairo are correctly installed.")
        print("If plotting to file, ensure 'pycairo' is installed ('pip install pycairo').")
        print("For GEXF reading issues, ensure 'libxml2-dev' is installed system-wide before installing python-igraph.")

if __name__ == "__main__":
    file_path = '/home/eduardo/Graph-creation-with-html/Graph-creation-with-html/graphs/camara/grafo_2024.gexf'
    
    print("--- Plotting Large Graph: Attempt 1 (Optimized for speed/memory, improved scaling) ---")
    plot_gexf_graph(file_path, 
                    layout_algorithm='fr', 
                    show_labels=False,      
                    node_size=5,             # Slightly larger nodes than before
                    edge_width=0.2,          # Slightly thicker edges
                    figure_size=(15,15),     # Figure size in inches for saved image aspect
                    output_filename="grafo_2024_plot_scaled.png", # New filename
                    dpi=150)                 # Increased DPI for better quality saved image

    # To try interactive plotting (might be slow/memory intensive)
    # print("\n--- Plotting Large Graph: Attempt 2 (Interactive - Optimized) ---")
    # plot_gexf_graph(file_path,
    #                 layout_algorithm='fr',
    #                 show_labels=False,
    #                 node_size=5,
    #                 edge_width=0.2,
    #                 figure_size=(12,12), # Inches for screen display
    #                 dpi=100) # DPI for screen display

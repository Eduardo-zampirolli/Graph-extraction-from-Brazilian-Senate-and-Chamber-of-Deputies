#include <igraph.h>
#include <stdio.h>

int main() {
    igraph_t graph;
    igraph_vector_int_t edges;
    
    // Create a full graph with 5 vertices
    igraph_full(&graph, 5, IGRAPH_UNDIRECTED, IGRAPH_NO_LOOPS);
    
    // Print some basic info
    printf("Vertices: %ld\n", (long)igraph_vcount(&graph));
    printf("Edges: %ld\n", (long)igraph_ecount(&graph));
    
    // Clean up
    igraph_destroy(&graph);
    
    return 0;
}
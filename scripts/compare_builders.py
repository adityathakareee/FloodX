"""Compare edge differences between old naive snapping and new topology-aware snapping."""
import sys
import os
sys.path.insert(0, os.path.abspath("backend"))

import pandas as pd
import networkx as nx
from app.services.routing.graph_builder import road_graph_builder

G_old = road_graph_builder.build_graph()
print(f"Old DiGraph: {G_old.number_of_nodes()} nodes, {G_old.number_of_edges()} edges")

# Let's count how many edges in G_old were oneway vs bidirectional
old_fwd = 0
old_bidir = 0
for u, v, d in G_old.edges(data=True):
    if d.get("is_oneway"):
        old_fwd += 1
    else:
        old_bidir += 1
print(f"Old DiGraph edges: {old_fwd} oneway, {old_bidir} bidirectional (total: {old_fwd + old_bidir})")

# Let's see how many self-loops were skipped in G_old
# We can check split_segments


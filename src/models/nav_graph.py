# Import required libraries
import json  # For reading JSON navigation data files
import networkx as nx  # For graph operations and pathfinding
from typing import List, Dict, Any, Tuple  # Type hints for better code clarity

class NavGraph:
    """Class representing a navigation graph with vertices and lanes"""
    def __init__(self, json_path: str):
        # Initialize empty lists and graph structure
        self.vertices: List[List] = []  # Store vertex information from JSON
        self.lanes: List[Tuple[Tuple[int, int], Dict]] = []  # Store lane information with metadata
        self.graph = nx.DiGraph()  # Create directed graph using networkx
        self.load_graph(json_path)  # Load graph data from JSON file

    def load_graph(self, json_path: str):
        """Load and parse graph data from JSON file"""
        with open(json_path, 'r') as f:  # Open JSON file for reading
            data = json.load(f)  # Parse JSON data into Python dictionary
            level = data['levels']['level1']  # Access level1 data from JSON
            self.vertices = level['vertices']  # Store vertex information
           
            # Process each lane in the level data
            for lane in level['lanes']:
                if len(lane) >= 3:  # Check if lane has metadata (3 or more elements)
                    lane_tuple = (lane[0], lane[1])  # Extract start and end vertices
                    metadata = lane[2] if isinstance(lane[2], dict) else {}  # Get metadata if it exists
                    self.lanes.append((lane_tuple, metadata))  # Store lane info with metadata
                    self.graph.add_edge(lane[0], lane[1], **metadata)  # Add edge to graph with metadata
                else:  # Handle lanes without metadata
                    lane_tuple = (lane[0], lane[1])  # Extract start and end vertices
                    self.lanes.append((lane_tuple, {}))  # Store lane info with empty metadata
                    self.graph.add_edge(lane[0], lane[1])  # Add edge to graph without metadata

    def get_shortest_path(self, start: int, end: int) -> List[int]:
        """Calculate shortest path between two vertices using A* algorithm"""
        try:
            return nx.astar_path(self.graph, start, end)  # Find path using A* algorithm
        except nx.NetworkXNoPath:
            return []  # Return empty list if no path exists

    def get_vertex_data(self, idx: int) -> Dict[str, Any]:
        """Retrieve metadata for a vertex by its index"""
        if 0 <= idx < len(self.vertices):  # Check if vertex index is valid
            return self.vertices[idx][2] if len(self.vertices[idx]) > 2 else {}  # Return metadata if it exists
        return {}  # Return empty dict if vertex doesn't exist

    def is_lane_available(self, lane: Tuple[int, int]) -> bool:
        """Check if lane exists in the graph"""
        return self.graph.has_edge(lane[0], lane[1])  # Check if edge exists between vertices
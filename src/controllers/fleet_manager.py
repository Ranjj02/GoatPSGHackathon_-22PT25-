from models.robot import Robot
from typing import List, Dict, Optional, Any
import threading 
from threading import Lock 

class FleetManager:
    """Class responsible for managing a fleet of robots and their operations"""
    
    def __init__(self, traffic_manager):
        # List to store all robots in the fleet
        self.robots: List[Robot] = []
        # Store reference to traffic manager for coordinating robot movements
        self.traffic_manager = traffic_manager
        # ID of currently selected robot (if any)
        self.selected_robot: Optional[int] = None
        # Counter for generating unique robot IDs
        self.next_id = 1
        # Thread lock for thread-safe operations
        self._lock = Lock()

    # def spawn_robot(self, vertex_idx: int, nav_graph) -> Robot:
    #     """Create new robot with proper dependencies"""
    #     robot = Robot(self.next_id, vertex_idx, nav_graph)
    #     self.robots.append(robot)
    #     self.next_id += 1
    #     return robot

    def spawn_robot(self, vertex_idx: int, nav_graph) -> Robot:
        """Thread-safe robot creation"""
        # Create new robot instance with unique ID, starting position, and navigation graph
        robot = Robot(self.next_id, vertex_idx, nav_graph)
        
        # Use lock to safely modify shared resources
        with self._lock:
            # Add robot to fleet
            self.robots.append(robot)
            # Increment ID counter for next robot
            self.next_id += 1
            
        # Log robot creation
        self._log(f"✅ Robot {robot.id} spawned at vertex {vertex_idx}")
        return robot

    def update_robots(self, delta_time: float):
        """Update all robots with traffic manager"""
        # Update each robot's state based on elapsed time
        for robot in self.robots:
            # Pass traffic manager to handle collision avoidance
            robot.update(self.traffic_manager, delta_time)

    # def assign_task(self, robot_id: int, destination_idx: int) -> bool:
    #     """Assign destination to specific robot"""
    #     robot = self.get_robot(robot_id)
    #     if robot:
    #         return robot.assign_task(destination_idx)
    #     return False
    def assign_task(self, robot_id: int, destination_idx: int) -> Dict[str, Any]:
        """Assign a destination task to a specific robot"""
        # Find robot by ID
        robot = self.get_robot(robot_id)
        
        # Return error if robot not found
        if not robot:
            return {
                'success': False,
                'message': f"Robot {robot_id} not found",
                'estimated_time': 0,
                'path': []
            }

        # Check if robot is currently charging
        if robot.status == "charging":
            return {
                'success': False,
                'message': f"Robot {robot_id} is charging (battery: {robot.battery:.1f}%)",
                'estimated_time': 0,
                'path': []
            }

        # Get navigation graph from robot
        nav_graph = robot.nav_graph
        if not nav_graph:
            return {
                'success': False,
                'message': "No navigation graph available",
                'estimated_time': 0,
                'path': []
            }

        # Calculate shortest path to destination
        path = nav_graph.get_shortest_path(robot.current_vertex, destination_idx)
        if not path:
            return {
                'success': False,
                'message': f"No valid path to Vertex {destination_idx}",
                'estimated_time': 0,
                'path': []
            }

        # Attempt to assign task to robot
        success = robot.assign_task(destination_idx)
        # Return result with path and estimated completion time
        return {
            'success': success,
            'message': f"Assignment {'succeeded' if success else 'failed'}",
            'estimated_time': len(path) * 1.0,  # Estimate 1 second per vertex
            'path': path
        }

    def get_robot(self, robot_id: int) -> Optional[Robot]:
        """Get robot by ID"""
        # Find and return robot with matching ID, or None if not found
        return next((r for r in self.robots if r.id == robot_id), None)

    def select_robot(self, robot_id: Optional[int]):
        """Select/deselect a robot"""
        # Update currently selected robot ID
        self.selected_robot = robot_id

    def clear_robots(self):
        """Reset the fleet"""
        # Remove all robots from fleet
        self.robots.clear()
        # Reset ID counter
        self.next_id = 1
        # Clear selected robot
        self.selected_robot = None
    def _log(self, message: str):
        """Thread-safe logging"""
        # Use lock to ensure thread-safe logging
        with self._lock:
            print(message)  # Print message (could be modified to write to file)
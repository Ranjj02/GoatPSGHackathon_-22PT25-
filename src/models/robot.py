import time
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass

@dataclass
class RobotConfig:
    battery_drain_rate: float = 0.5
    charge_rate: float = 2.0
    min_battery: float = 20.0
    max_wait_time: float = 10.0
    movement_speed: float = 1.0

class Robot:
    def __init__(self, robot_id: int, start_vertex_idx: int, nav_graph, config: RobotConfig = RobotConfig()):
        self.id = robot_id
        self.current_vertex = start_vertex_idx
        self.destination: Optional[int] = None
        self.path: List[int] = []
        self.status = "idle"
        self.battery = 100.0
        self.last_update_time = time.time()
        self.wait_start_time: Optional[float] = None
        self.config = config
        self.nav_graph = nav_graph
        self.color = self._generate_color(robot_id)
        self.current_lane: Optional[Tuple[int, int]] = None
        self.progress = 0.0
        self.log = []
        with open("fleet_logs.txt", "a") as f:
            f.write(f"Initialized Robot {self.id}\n")
            pass
      # Clear log file on init

    def _generate_color(self, robot_id: int) -> Tuple[int, int, int]:
        return ((robot_id * 50) % 256, (robot_id * 100) % 256, (robot_id * 150) % 256)

    # def assign_task(self, destination_idx: int) -> bool:
    #     if self.status in ["charging", "error"]:
    #         self._log(f"Failed task assignment - Status: {self.status}")
    #         return False
            
    #     self.destination = destination_idx
    #     self._log(f"New task assigned to vertex {destination_idx}")
    #     self._calculate_path()
        
        # if self.path:
        #     self.status = "moving"
        #     return True
        # return False
    #def assign_task(self, destination_idx: int) -> bool:
        # """
        # Assigns a new destination to the robot with traffic awareness
        # Returns:
        #     bool: True if task was successfully assigned, False otherwise
        # """
        # # Status check
        # if self.status in ["charging", "error"]:
        #     self._log(f"Failed task assignment - Status: {self.status}")
        #     return False

        # # Store destination
        # self.destination = destination_idx
        # self._log(f"New task assigned to vertex {destination_idx}")

        # # Calculate path (this will automatically update self.path)
        # self._calculate_path()

        # # Verify path exists
        # if not self.path:
        #     self._log("No valid path to destination")
        #     return False

        # # Check if first lane is available
        # if len(self.path) > 1:
        #     first_lane = (self.path[0], self.path[1])
        #     if not self.nav_graph.is_lane_available(first_lane):
        #         self._log(f"Initial lane {first_lane} is blocked")
        #         return False

        # # Reset movement state
        # self.progress = 0.0
        # self.current_lane = None
        # self.status = "moving"
        # self.wait_start_time = None

        # self._log(f"Navigation started to vertex {destination_idx}")
        # return True
    def assign_task(self, destination_idx: int) -> bool:
        """Updated version with path validation"""
        if self.status in ["charging", "error"]:
            self._log(f"Cannot assign task - Status: {self.status}")
            return False

        self.destination = destination_idx
        self._calculate_path()  # This should populate self.path
        
        if not self.path:
            self._log(f"No valid path to vertex {destination_idx}")
            return False

        # Reset movement state
        self.progress = 0.0
        self.current_lane = None
        self.status = "moving"
        self.wait_start_time = None
        
        self._log(f"Assigned to vertex {destination_idx} via path: {self.path}")
        return True
    def _calculate_path(self):
        if self.destination is not None:
            self.path = self.nav_graph.get_shortest_path(self.current_vertex, self.destination)
            if not self.path:
                self.status = "error"

    def update(self, traffic_manager, delta_time: float) -> bool:
        changed = False

        if self._check_imminent_collision(traffic_manager, delta_time):
            self.status = "emergency_stop"

        if self.status == "charging":
            self._handle_charging(delta_time)
        elif self.status == "error":
            pass
        elif self.battery < self.config.min_battery:
            self._handle_low_battery()
        elif self.status == "moving":
            changed = self._handle_movement(traffic_manager, delta_time)
            if self._check_imminent_collision(traffic_manager, delta_time):  # Pass delta_time
                self.status = "emergency_stop"
        elif self.status == "waiting":
            changed = self._handle_waiting(time.time())

        self.last_update_time = time.time()
        return changed
    
    def _check_imminent_collision(self, traffic_manager, delta_time: float) -> bool:
        """Predict collisions 1 second ahead"""
        if not self.current_lane or len(self.path) < 2:
            return False
            
        # Get next lane in path
        next_lane = (self.path[0], self.path[1])
        
        # Check if lane will be occupied based on current progress + movement speed
        progress_in_1sec = self.progress + (self.config.movement_speed * delta_time)
        if progress_in_1sec >= 1.0:  # Will reach next vertex within 1 second
            return traffic_manager.is_lane_occupied(next_lane)
        return False
   # models/robot.py (updated movement handling only)
    def _handle_movement(self, traffic_manager, delta_time: float) -> bool:
        if not self.path:
            self._log("Movement failed - No path available")
            return False

        next_vertex = self.path[0]
        lane = (self.current_vertex, next_vertex)

        # Only request lane if we don't already have it
        if self.current_lane != lane:
            if traffic_manager.request_lane(self.id, lane):
                self.current_lane = lane
                self.progress = 0.0
            else:
                if self.status != "waiting":
                    self.wait_start_time = time.time()
                    self.status = "waiting"
                return False

        # Perform movement
        self.progress += delta_time * self.config.movement_speed
        if self.progress >= 1.0:
            self.current_vertex = next_vertex
            self.path.pop(0)
            self.progress = 0.0
            if self.current_lane:
                traffic_manager.release_lane(self.current_lane)
                self.current_lane = None

            if not self.path:
                self.status = "idle"
            return True

        self.battery = max(0, self.battery - self.config.battery_drain_rate * delta_time)
        return True
    
    def _handle_waiting(self, current_time: float) -> bool:
        """Handle waiting timeout"""
        if (self.wait_start_time and 
            (current_time - self.wait_start_time) > self.config.max_wait_time):
            self._calculate_path()
            self.status = "moving"
            self._log("Replanning path after timeout")
            return True
        return False

    def _is_at_charger(self) -> bool:
        """Check if robot is at charging station"""
        vertex_data = self.nav_graph.get_vertex_data(self.current_vertex)
        return vertex_data.get("is_charger", False)

   
    def _log(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] Robot {self.id}: {message}"
        self.log.append(log_entry)
        with open("fleet_logs.txt", "a") as f:
            f.write(log_entry + "\n")
        print(log_entry)

    def get_status(self) -> Dict[str, Any]:
        """Get current robot status"""
        return {
            "id": self.id,
            "current_vertex": self.current_vertex,
            "destination": self.destination,
            "status": self.status,
            "battery": f"{self.battery:.1f}%",
            "path": self.path.copy(),
            "color": self.color,
            "current_lane": self.current_lane,
            "progress": self.progress
        }

    def get_position(self) -> Tuple[float, float]:
        """Get interpolated position for smooth rendering"""
        if not self.current_lane or not self.nav_graph.vertices:
            return self.nav_graph.vertices[self.current_vertex][:2]
        
        start = self.nav_graph.vertices[self.current_lane[0]]
        end = self.nav_graph.vertices[self.current_lane[1]]
        return (
            start[0] + (end[0] - start[0]) * self.progress,
            start[1] + (end[1] - start[1]) * self.progress
        )
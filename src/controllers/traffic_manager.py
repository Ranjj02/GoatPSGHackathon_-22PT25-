# controllers/traffic_manager.py (updated)
import time
from enum import Enum, auto
from typing import Dict, Tuple, List, Any, Set

class LaneEvent(Enum):
    GRANTED = auto()
    RELEASED = auto()
    QUEUED = auto()
    TIMEOUT = auto()
    BLOCKED = auto()

class TrafficManager:
    def __init__(self):
        self.occupied_lanes: Dict[Tuple[int, int], int] = {}  # {lane: robot_id}
        self.waiting_queues: Dict[Tuple[int, int], List[int]] = {}  # FIFO queues
        self.occupation_timestamps: Dict[Tuple[int, int], float] = {}
        self.last_deadlock_check = time.time()

    # In controllers/traffic_manager.py (inside TrafficManager class)
    def is_lane_available(self, lane: Tuple[int, int]) -> bool:
        """Check if lane and reverse lane are free"""
        return (
            lane not in self.occupied_lanes and 
            (lane[1], lane[0]) not in self.occupied_lanes
        )

    def request_lane(self, robot_id: int, lane: Tuple[int, int]) -> bool:
        """Request lane access with deadlock prevention"""
        
        lane = tuple(lane) if isinstance(lane, list) else lane
        current_time = time.time()

        if self.detect_collisions(lane):
            self._log_event(LaneEvent.BLOCKED, robot_id, lane)
            return False
        
        # Check if lane is available
        if lane not in self.occupied_lanes and (lane[1], lane[0]) not in self.occupied_lanes:
            self.occupied_lanes[lane] = robot_id
            self.occupation_timestamps[lane] = current_time
            return True
            
        # If not available, add to queue
        if lane not in self.waiting_queues:
            self.waiting_queues[lane] = []
        if robot_id not in self.waiting_queues[lane]:
            self.waiting_queues[lane].append(robot_id)
        return False

    def release_lane(self, lane: Tuple[int, int]):
        """Release lane and process queue"""
        if lane in self.occupied_lanes:
            del self.occupied_lanes[lane]
            if lane in self.occupation_timestamps:
                del self.occupation_timestamps[lane]
            
        # Process queue if any robots waiting
        if lane in self.waiting_queues and self.waiting_queues[lane]:
            next_robot = self.waiting_queues[lane].pop(0)
            # Don't automatically grant - let robot request again

    def update_movement_status(self, lane: Tuple[int, int], robot_id: int, is_moving: bool):
        """Track movement status (no changes needed)"""
        pass

    def _perform_periodic_checks(self):
        """Check for timeouts (called from robot update)"""
        current_time = time.time()
        if current_time - self.last_deadlock_check > 2.0:
            self.last_deadlock_check = current_time
            stale_lanes = [
                lane for lane, ts in self.occupation_timestamps.items()
                if current_time - ts > 5.0
            ]
            for lane in stale_lanes:
                self.release_lane(lane)

    def _is_lane_available(self, lane: Tuple[int, int]) -> bool:
        """Check lane availability considering bidirectional traffic"""
        reverse_lane = (lane[1], lane[0])
        return (
            lane not in self.occupied_lanes and
            reverse_lane not in self.occupied_lanes
        )

    def _grant_access(self, robot_id: int, lane: Tuple[int, int]):
        """Grant lane access to robot"""
        self.occupied_lanes[lane] = robot_id
        self.occupation_timestamps[lane] = time.time()
        self._remove_from_other_queues(robot_id)

    def _enqueue_robot(self, robot_id: int, lane: Tuple[int, int]):
        """Add robot to waiting queue"""
        if lane not in self.waiting_queues:
            self.waiting_queues[lane] = []
        if robot_id not in self.waiting_queues[lane]:
            self.waiting_queues[lane].append(robot_id)

    def _process_queue(self, lane: Tuple[int, int]):
        """Process waiting queue when lane becomes available"""
        if lane in self.waiting_queues and self.waiting_queues[lane]:
            next_robot = self.waiting_queues[lane].pop(0)

    def _remove_from_other_queues(self, robot_id: int):
        """Remove robot from all queues when granted access"""
        for queue in self.waiting_queues.values():
            if robot_id in queue:
                queue.remove(robot_id)

    def _resolve_issues(self):
        """Handle timeouts and deadlocks"""
        current_time = time.time()
        # Clear stale lanes
        stale_lanes = [
            lane for lane, t in self.occupation_timestamps.items()
            if current_time - t > 5.0  # 5 second timeout
        ]
        for lane in stale_lanes:
            self._log_event(LaneEvent.TIMEOUT, self.occupied_lanes[lane], lane)
            self.release_lane(lane)
        
        # Check for deadlocks
        deadlocked_robots = self._find_deadlocks()
        for robot_id in deadlocked_robots:
            # Implement deadlock resolution logic here
            pass

    def _find_deadlocks(self) -> Set[int]:
        """Identify robots involved in circular waits"""
        # Placeholder implementation - returns empty set
        return set()
    def _log_event(self, event_type: LaneEvent, robot_id: int, lane: Tuple[int, int]):
        """Log traffic events with proper timestamp formatting"""
        if not hasattr(self, 'event_log'):
            self.event_log = []
        
    # Use the parameter name correctly (should match the definition)
        log_entry = {
            "timestamp": time.time(),
            "event": event_type.name,  # Now using the parameter 'event_type'
            "robot_id": robot_id,
            "lane": lane
        }
        self.event_log.append(log_entry)
    
    # Formatted print statement
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print(f"[{timestamp}] {event_type.name}: Robot {robot_id} on lane {lane}")

    def clear_queues(self):
        """Reset all waiting queues (for simulation reset)"""
        self.waiting_queues.clear()

    def detect_collisions(self, lane: Tuple[int, int] = None) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        Check for potential collisions
        Args:
            lane: Optional specific lane to check (None checks all lanes)
        Returns:
            List of colliding lane pairs
        """
        collisions = []
        occupied_set = set(self.occupied_lanes.keys())
        
        # If checking specific lane
        if lane is not None:
            reverse_lane = (lane[1], lane[0])
            if reverse_lane in occupied_set:
                return [(lane, reverse_lane)]
            return []
        
        # Check all lanes
        for lane in occupied_set:
            reverse_lane = (lane[1], lane[0])
            if reverse_lane in occupied_set:
                collisions.append((lane, reverse_lane))
    
        return collisions

    def resolve_deadlocks(self):
        """Force-release lanes in deadlock situations"""
        for lane in list(self.occupied_lanes.keys()):
            if time.time() - self.occupation_timestamps.get(lane, 0) > 5:  # 5 sec timeout
                self.release_lane(lane)
                self._log_event(LaneEvent.TIMEOUT, self.occupied_lanes[lane], lane)
    
    def is_lane_occupied(self, lane: Tuple[int, int]) -> bool:
        """Check if a specific lane is currently occupied"""
        lane = tuple(lane) if isinstance(lane, list) else lane
        return lane in self.occupied_lanes
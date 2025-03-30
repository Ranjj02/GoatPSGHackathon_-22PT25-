import pygame
import time
import math
from typing import Optional, Tuple
from models.nav_graph import NavGraph
from controllers.fleet_manager import FleetManager
from controllers.traffic_manager import TrafficManager
from models.robot import Robot

class FleetGUI:
    def __init__(self, nav_graph: NavGraph, fleet_manager: FleetManager, traffic_manager: TrafficManager):
        self.nav_graph = nav_graph
        self.fleet = fleet_manager
        self.traffic = traffic_manager
        self._init_pygame()
        self._init_visuals()
        
    def _init_pygame(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1200, 800))
        pygame.display.set_caption("Fleet Management System")
        self.clock = pygame.time.Clock()
        self.last_frame_time = time.time()

    def _init_visuals(self):
        self.vertex_radius = 10
        self.robot_radius = 8
        self.scale, self.offset = self._calculate_auto_scale()
        self.font_small = pygame.font.SysFont('Arial', 12)
        self.font_medium = pygame.font.SysFont('Arial', 14, bold=True)
        self.font_large = pygame.font.SysFont('Arial', 18)

    def run(self):
        """Main GUI loop"""
        running = True
        while running:
            delta_time = self._handle_events()
            self._update(delta_time)
            self._draw()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()

    def _handle_events(self) -> float:
        """Process events and return delta time"""
        current_time = time.time()
        delta_time = current_time - self.last_frame_time
        self.last_frame_time = current_time
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_click(event)
        return delta_time

    def _handle_click(self, event):
        """Handle mouse clicks"""
        mouse_pos = pygame.mouse.get_pos()
        vertex_idx = self._get_nearest_vertex(mouse_pos)
        
        if event.button == 1:  # Left click
            robot = self._get_robot_at_vertex(vertex_idx)
            if robot:
                self.fleet.select_robot(robot.id)
            else:
                new_robot = self.fleet.spawn_robot(vertex_idx, self.nav_graph)
                self.fleet.select_robot(new_robot.id)
                
        elif event.button == 3:  # Right click
            if self.fleet.selected_robot:
                self.fleet.assign_task(self.fleet.selected_robot, vertex_idx)

    def _update(self, delta_time: float):
        """Update simulation state"""
        self.fleet.update_robots(delta_time)

    def _draw(self):
        """Render all elements"""
        self.screen.fill((255, 255, 255))  # White background
        
        # Draw instructions
        self._draw_instructions()
        
        # Draw navigation elements
        self._draw_lanes()
        self._draw_vertices()
        self._draw_robots()
        self._draw_alerts()
        self._draw_log_panel()

        self._draw_traffic_alerts()
        self._draw_collision_warnings()

    def _draw_traffic_alerts(self):
        """Show lane occupancy warnings"""
        for lane in self.traffic.occupied_lanes:
            start = self._to_screen_coords(self.nav_graph.vertices[lane[0]])
            end = self._to_screen_coords(self.nav_graph.vertices[lane[1]])
            pygame.draw.line(self.screen, (255, 100, 100), start, end, 4)  # Red highlight

    def _draw_collision_warnings(self):
        """Show collision markers"""
        for lane1, lane2 in self.traffic.detect_collisions():
            center1 = self._get_lane_center(lane1)
            center2 = self._get_lane_center(lane2)
            pygame.draw.circle(self.screen, (255, 0, 0), center1, 10)
            pygame.draw.circle(self.screen, (255, 0, 0), center2, 10)

    def _draw_notifications(self):
        """Show pop-up alerts"""
        alerts = []
        
        # Check for robots that have been waiting too long
        for robot in self.fleet.robots:
            if robot.status == "waiting" and time.time() - robot.wait_start_time > 2:
                alerts.append(f"Robot {robot.id} blocked at Vertex {robot.current_vertex}")
        
        # Display last 3 alerts
        for i, alert in enumerate(alerts[-3:]):
            alert_surf = pygame.Surface((300, 30))                    # Create surface for alert
            alert_surf.fill((255, 200, 200))                         # Light red background
            text = self.font_medium.render(alert, True, (200, 0, 0)) # Red text
            alert_surf.blit(text, (5, 5))                            # Draw text on alert surface
            self.screen.blit(alert_surf, (self.screen.get_width() - 310, 10 + i * 35))  # Position alert on screen

    def _draw_log_panel(self):
        """Draw panel showing recent robot activities"""
        log_surface = pygame.Surface((400, 200))           # Create surface for log panel
        log_surface.fill((240, 240, 240))                 # Light gray background
        
        # Collect recent logs from all robots
        all_logs = []
        for robot in self.fleet.robots:
            all_logs.extend(robot.log[-2:])               # Get last 2 entries from each robot
        
        # Display last 5 log entries
        for i, entry in enumerate(sorted(all_logs, reverse=True)[:5]):
            text = self.font_small.render(entry[:50], True, (0, 0, 0))  # Render log text
            log_surface.blit(text, (10, 10 + i * 20))                   # Position text in log panel
        
        # Position log panel on screen
        self.screen.blit(log_surface, (self.screen.get_width() - 410, 10))

    def _draw_instructions(self):
        """Draw control instructions at top of screen"""
        instructions = [
            "Left Click: Select/Create Robot",         # Explain left click functionality
            "Right Click: Send Robot to Vertex",       # Explain right click functionality
            f"Total Robots: {len(self.fleet.robots)}", # Show total number of robots
            f"Selected Robot: {self.fleet.selected_robot if self.fleet.selected_robot else 'None'}"  # Show currently selected robot
        ]
        
        # Draw each instruction line
        for i, text in enumerate(instructions):
            text_surface = self.font_large.render(text, True, (0, 0, 0))  # Create text surface in black
            self.screen.blit(text_surface, (10, 10 + i * 25))            # Position text with 25px vertical spacing

    def _draw_lanes(self):
        """Draw navigation lanes between vertices"""
        for (start_end, meta) in self.nav_graph.lanes:
            # Convert vertex coordinates to screen coordinates
            start_pos = self._to_screen_coords(self.nav_graph.vertices[start_end[0]])
            end_pos = self._to_screen_coords(self.nav_graph.vertices[start_end[1]])
            
            # Choose lane color: red if occupied, blue if free
            color = (255, 0, 0) if start_end in self.traffic.occupied_lanes else (0, 0, 255)
            pygame.draw.line(self.screen, color, start_pos, end_pos, 2)  # Draw the lane
            
            # Draw queue size if robots are waiting
            if start_end in self.traffic.waiting_queues:
                queue_count = len(self.traffic.waiting_queues[start_end])
                if queue_count > 0:
                    # Show number of waiting robots in orange
                    text = self.font_small.render(str(queue_count), True, (255, 69, 0))
                    self.screen.blit(text, (
                        (start_pos[0] + end_pos[0]) // 2,  # Position text at middle of lane
                        (start_pos[1] + end_pos[1]) // 2
                    ))

    def _draw_vertices(self):
        """Draw all vertices (nodes) in the navigation graph"""
        for i, vertex in enumerate(self.nav_graph.vertices):
            pos = self._to_screen_coords(vertex)  # Convert to screen coordinates
            # Choose vertex color: green for chargers, red for normal vertices
            color = (0, 255, 0) if vertex[2].get('is_charger') else (255, 0, 0)
            pygame.draw.circle(self.screen, color, pos, self.vertex_radius)  # Draw vertex circle
            
            # Draw vertex ID in white
            text_id = self.font_medium.render(str(i), True, (255, 255, 255))
            self.screen.blit(text_id, (pos[0] - 5, pos[1] - 7))
            
            # Draw vertex name below circle if it exists
            if len(vertex) > 2 and 'name' in vertex[2]:
                text_name = self.font_small.render(vertex[2]['name'], True, (0, 0, 0))
                self.screen.blit(text_name, (pos[0] - 15, pos[1] + 15))
            
            # Mark intersections (vertices with >2 connections) with a black square
            connections = sum(1 for lane in self.nav_graph.lanes if i in lane)
            if connections > 2:
                pygame.draw.rect(self.screen, (0, 0, 0), (pos[0] - 3, pos[1] - 3, 6, 6))

    def _draw_robots(self):
        """Draw all robots with IDs"""
        for robot in self.fleet.robots:
            pos = self._to_screen_coords(self.nav_graph.vertices[robot.current_vertex])
            if robot.status == "charging":
                pygame.draw.polygon(self.screen, (255, 255, 0), 
                    [(pos[0], pos[1] - 10), (pos[0] - 5, pos[1] + 5), (pos[0] + 5, pos[1] + 5)])  # ⚡
            elif robot.status == "waiting":
                pygame.draw.rect(self.screen, (255, 0, 0), (pos[0] - 5, pos[1] - 5, 10, 10), 1)  # □
            # Robot circle
            pygame.draw.circle(self.screen, robot.color, pos, self.robot_radius)
            
            # Selection highlight
            if robot.id == self.fleet.selected_robot:
                pygame.draw.circle(self.screen, (255, 255, 255), pos, self.robot_radius + 2, 2)
            
            # Robot ID
            text = self.font_small.render(str(robot.id), True, (0, 0, 0))  # Black text
            text_rect = text.get_rect(center=pos)
            self.screen.blit(text, text_rect)

    def _draw_alerts(self):
        alert_msg = None
        for robot in self.fleet.robots:
            if robot.status == "waiting" and time.time() - robot.wait_start_time > 5:
                alert_msg = f"Robot {robot.id} blocked at vertex {robot.current_vertex}"
        
        if alert_msg:
            alert_surface = pygame.Surface((400, 40))
            alert_surface.fill((255, 200, 200))
            text = self.font_large.render(alert_msg, True, (255, 0, 0))
            alert_surface.blit(text, (10, 10))
            self.screen.blit(alert_surface, (self.screen.get_width() // 2 - 200, 10))

    def _to_screen_coords(self, vertex) -> Tuple[int, int]:
        """Convert graph coordinates to screen coordinates"""
        return (
            int(vertex[0] * self.scale + self.offset[0]),  # Scale and offset X coordinate
            int(vertex[1] * self.scale + self.offset[1])   # Scale and offset Y coordinate
        )

    def _get_nearest_vertex(self, mouse_pos) -> int:
        """Find closest vertex to mouse position"""
        graph_x = (mouse_pos[0] - self.offset[0]) / self.scale
        graph_y = (mouse_pos[1] - self.offset[1]) / self.scale
        
        return min(
            range(len(self.nav_graph.vertices)),
            key=lambda i: (
                (self.nav_graph.vertices[i][0] - graph_x)**2 + 
                (self.nav_graph.vertices[i][1] - graph_y)**2
            )
        )

    def _get_robot_at_vertex(self, vertex_idx: int) -> Optional[Robot]:
        """Get robot at specified vertex"""
        return next((r for r in self.fleet.robots if r.current_vertex == vertex_idx), None)

    def _calculate_auto_scale(self) -> Tuple[float, Tuple[float, float]]:
        """Calculate appropriate scale and offset to fit graph on screen"""
        if not self.nav_graph.vertices:
            return 1.0, (0, 0)  # Default values if no vertices
            
        # Find bounds of graph
        min_x = min(v[0] for v in self.nav_graph.vertices)
        max_x = max(v[0] for v in self.nav_graph.vertices)
        min_y = min(v[1] for v in self.nav_graph.vertices)
        max_y = max(v[1] for v in self.nav_graph.vertices)
        
        # Calculate scale to fit graph on screen with margins
        scale = min(
            (self.screen.get_width() - 200) / (max_x - min_x) if (max_x - min_x) > 0 else 50,
            (self.screen.get_height() - 200) / (max_y - min_y) if (max_y - min_y) > 0 else 50
        ) * 0.9  # 90% of maximum possible scale for margin
        
        # Calculate offset to center graph
        offset = (100 - min_x * scale, 100 - min_y * scale)
        return scale, offset
    
    def _get_lane_center(self, lane: Tuple[int, int]) -> Tuple[int, int]:
        """Get the center point of a lane for collision markers"""
        start_pos = self._to_screen_coords(self.nav_graph.vertices[lane[0]])
        end_pos = self._to_screen_coords(self.nav_graph.vertices[lane[1]])
        return (
            (start_pos[0] + end_pos[0]) // 2,
            (start_pos[1] + end_pos[1]) // 2
        )
    
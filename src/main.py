import pygame
import sys
from models.nav_graph import NavGraph
from controllers.traffic_manager import TrafficManager
from controllers.fleet_manager import FleetManager
from gui.fleet_gui import FleetGUI

def main():
    # Initialize
    pygame.init()
    screen = pygame.display.set_mode((1000, 800))  # Larger window
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('Arial', 20, bold=True)
    
    # Load graph and managers
    nav_graph = NavGraph("data/nav_graph.json")
    traffic_manager = TrafficManager()
    fleet_manager = FleetManager(traffic_manager)  # Pass TrafficManager here
    
    gui = FleetGUI(nav_graph, fleet_manager, traffic_manager)
    gui.run()
        
    # Debug print vertex data
    print("Vertex Data Sample:")
    for i, v in enumerate(nav_graph.vertices[:5]):
        print(f"Vertex {i}: {v}")

    print("\nCharging Stations:")
    for i, v in enumerate(nav_graph.vertices):
        if v[2].get("is_charger"):
            print(f"Vertex {i} is a charger")
    
    # Spawn test robot
    test_robot = fleet_manager.spawn_robot(0, nav_graph)
    test_robot.assign_task(4)  # Move to vertex 4 (charger)
    
    # Visualization parameters
    scale = 50  # Increased scale
    offset_x, offset_y = 100, 100  # Increased offset
    
    # Main loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Update all robots
        fleet_manager.update_robots(0.1)  # Pass delta time
        
        # Clear screen
        screen.fill((240, 240, 240))  # Light gray background
        
        # Draw lanes (edges)
        for lane in nav_graph.lanes:
            start_idx, end_idx = lane
            start_x, start_y, _ = nav_graph.vertices[start_idx]
            end_x, end_y, _ = nav_graph.vertices[end_idx]
            
            screen_start = (int(start_x*scale + offset_x), int(-start_y*scale + offset_y))
            screen_end = (int(end_x*scale + offset_x), int(-end_y*scale + offset_y))    
            pygame.draw.line(screen, (150, 150, 150), screen_start, screen_end, 3)
        
        # Draw vertices (nodes)
        for i, vertex in enumerate(nav_graph.vertices):
            x, y, meta = vertex
            screen_x = int(x*scale + offset_x)
            screen_y = int(-y*scale + offset_y)
            
            # Set color based on properties
            if meta.get("is_charger"):
                color = (50, 200, 50)  # Green for chargers
                radius = 12
            else:
                color = (70, 70, 200)  # Blue for normal
                radius = 10
                
            pygame.draw.circle(screen, color, (screen_x, screen_y), radius)
            
            # Draw vertex index (black text)
            text = font.render(str(i), True, (0, 0, 0))
            text_rect = text.get_rect(center=(screen_x, screen_y))
            screen.blit(text, text_rect)
        
        # Draw robots
        for robot in fleet_manager.robots:
            x, y, _ = nav_graph.vertices[robot.current_vertex]
            screen_x = int(x*scale + offset_x)
            screen_y = int(-y*scale + offset_y)
            
            pygame.draw.circle(screen, robot.color, (screen_x, screen_y), 15)
            
            # Draw robot ID (white text)
            id_text = font.render(str(robot.id), True, (255, 255, 255))
            id_rect = id_text.get_rect(center=(screen_x, screen_y))
            screen.blit(id_text, id_rect)
        
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
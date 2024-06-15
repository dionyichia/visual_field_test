import pygame
import sys
import math

class Test_interface:
    def __init__(self, display_size=(1024,768)):

        # Set up the display
        width, height = display_size[0], display_size[1]
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Pygame Example")

        self.settings = {
            #Define test colours
            'screen_colour': (0,0,0),
            'main_ball_colour': (255,0,0),
            'secondary_ball_colour': (255,255,255),

            # Set up the balls
            'main_ball_radius': 15,
            'main_ball_position': (width // 2, height // 2),

            # Number of white balls and their properties
            'num_white_balls': 4,
            'white_ball_radius': 10,
            'white_ball_display_duration': 2000,  # duration in milliseconds
            'white_ball_delay': 3000,  # delay between each white ball appearance in milliseconds
        }

        # Calculate positions for the white balls in a circular pattern
        white_ball_positions = []
        for i in range(self.settings['num_white_balls']):
            angle = 2 * math.pi * i / self.settings['num_white_balls']
            x = self.settings['main_ball_position'][0] + 200 * math.cos(angle)
            y = self.settings['main_ball_position'][1] + 200 * math.sin(angle)
            white_ball_positions.append((x, y))
        
        self.white_ball_pos = white_ball_positions
    
    def update_test(self, start_time, current_time):
        screen = self.screen
        elapsed_time = current_time - start_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        
        # Fill the background with black
        screen = self.screen
        screen.fill(self.settings['screen_colour'])

        # Draw the main red ball
        pygame.draw.circle(screen, self.settings['main_ball_colour'], self.settings['main_ball_position'], self.settings['main_ball_radius'])

        # Determine which white ball to display
        ball_index = (elapsed_time // self.settings['white_ball_delay']) % ( self.settings['num_white_balls'] + 1)

        # Draw the white ball if it's not the last index
        if ball_index < self.settings['num_white_balls'] :
            pygame.draw.circle(screen, self.settings['secondary_ball_colour'], self.white_ball_pos[ball_index], self.settings['white_ball_radius'] )

        return True

if __name__ == "__main__":
    # Initialize Pygame
    pygame.init()
    start_time = pygame.time.get_ticks()
    interface = Test_interface((1048,768))
    running = True

    while running:
        current_time = pygame.time.get_ticks()
        running = Test_interface.update_test(interface, start_time, current_time)

        # Update the display
        pygame.display.flip()

    # Quit Pygame
    pygame.quit()
    sys.exit()
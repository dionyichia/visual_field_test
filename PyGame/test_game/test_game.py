import pygame
import sys
import math

# Define some colors
BLACK = (0, 0, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)

# Set up the display
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Pygame Example")

# Set up the balls
main_ball_radius = 15
main_ball_position = (width // 2, height // 2)

# Number of white balls and their properties
num_white_balls = 4
white_ball_radius = 10
white_ball_display_duration = 2000  # duration in milliseconds
white_ball_delay = 3000  # delay between each white ball appearance in milliseconds

# Calculate positions for the white balls in a circular pattern
white_ball_positions = []
for i in range(num_white_balls):
    angle = 2 * math.pi * i / num_white_balls
    x = main_ball_position[0] + 200 * math.cos(angle)
    y = main_ball_position[1] + 200 * math.sin(angle)
    white_ball_positions.append((x, y))

def start_test(start_time, current_time):
    elapsed_time = current_time - start_time

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False

    # Fill the background with black
    screen.fill(BLACK)

    # Draw the main red ball
    pygame.draw.circle(screen, RED, main_ball_position, main_ball_radius)

    # Determine which white ball to display
    ball_index = (elapsed_time // white_ball_delay) % (num_white_balls + 1)

    # Draw the white ball if it's not the last index
    if ball_index < num_white_balls:
        pygame.draw.circle(screen, WHITE, white_ball_positions[ball_index], white_ball_radius)

    return True

if __name__ == "__main__":
    # Initialize Pygame
    pygame.init()
    start_time = pygame.time.get_ticks()
    running = True

    while running:
        current_time = pygame.time.get_ticks()
        running = start_test(start_time, current_time)

        # Update the display
        pygame.display.flip()

    # Quit Pygame
    pygame.quit()
    sys.exit()
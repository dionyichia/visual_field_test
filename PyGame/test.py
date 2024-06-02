import pygame
import cv2

class Setup:
    def __init__(self, device=0, camres=(1280, 720), disptype='window', dispres=(1024, 768), display=None, zoom_factor=1.0):
        # Initialize the camera
        self.cap = cv2.VideoCapture(device)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, camres[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camres[1])
        self.zoom_factor = zoom_factor

        # Initialize Pygame
        pygame.init()
        if display is None:
            if disptype == 'window':
                self.disp = pygame.display.set_mode(dispres, pygame.RESIZABLE)
            elif disptype == 'fullscreen':
                self.disp = pygame.display.set_mode(dispres, pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
            else:
                raise ValueError("disptype must be 'window' or 'fullscreen'")
        else:
            self.disp = display
            dispres = self.disp.get_size()
        
        self.dispsize = dispres

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            raise Exception("Error in camtracker.Setup.get_frame: could not read frame from camera")
        
        if self.zoom_factor > 1.0:
            h, w, _ = frame.shape
            center_x, center_y = w // 2, h // 2
            radius_x, radius_y = int(w // (2 * self.zoom_factor)), int(h // (2 * self.zoom_factor))
            min_x, max_x = center_x - radius_x, center_x + radius_x
            min_y, max_y = center_y - radius_y, center_y + radius_y

            cropped_frame = frame[min_y:max_y, min_x:max_x]
            frame = cv2.resize(cropped_frame, (w, h), interpolation=cv2.INTER_LINEAR)
        
        return frame

    def display_frame(self):
        frame = self.get_frame()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, self.dispsize)
        frame = frame.swapaxes(0, 1)
        pygame_frame = pygame.surfarray.make_surface(frame)
        self.disp.blit(pygame_frame, (0, 0))
        pygame.display.update()

# Example usage
def available_devices():
    return [0]

# Initialization
setup = Setup(device=0, camres=(1920,1080), zoom_factor=8.0)

# Main loop
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    setup.display_frame()
    clock.tick(30)  # Limit to 30 frames per second

pygame.quit()
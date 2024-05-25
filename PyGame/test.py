import pygame
import pygame.camera

pygame.init()
pygame.camera.init()

cameras = pygame.camera.list_cameras()
if not cameras:
    print("No cameras found")
else:
    cam = pygame.camera.Camera(cameras[0], (640, 480))
    cam.start()

    screen = pygame.display.set_mode((640, 480))

    while True:
        image = cam.get_image()
        screen.blit(image, (0, 0))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cam.stop()
                pygame.quit()
                exit()
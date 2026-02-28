import time 
import pygame

def fw():
    print("Előre")

screen = pygame.display.set_mode((240, 240))
while True:
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                fw()
                print("Forward")
            if event.key == pygame.K_s:
                bw()
                print("Backward")
            if event.key == pygame.K_a:
                left()
                print("Left")
            if event.key == pygame.K_d:
                right()
                print("Right")
            if event.key == pygame.K_q:
                break
        if event.type == pygame.KEYUP:
            stop()
from gpiozero import Motor
import time 
import pygame

"""
The pins should be like this:
ALL THESE ARE GPIO x. 
For example: GPIO 14 - Right front forward

Right front forward: 14
Right front backward: 15
Left front fw: 24
Left front bw: 17

Right rear fw: 18
Right rear bw: 23
Left rear fw: 27
Left rear bw: 22
"""

# Defining the pins
# The naming scheme is Side Position Direction
# For example: RFF - Right Front Forward

RFF = 14
RFB = 15
LFF = 24
LFB = 17
RRF = 18
RRB = 23
LRF = 27
LRB = 22

# Setting up outputs

RF = Motor(RFF,RFB)
RR = Motor(RRF,RRB)
LF = Motor(LFF,LFB)
LR = Motor(LRF,LRB)

# Making functions for commands
# For example: Forward: RFF,LFF,RRF,LRF - HIGH

def fw():
    RF.forward()
    RR.forward()
    LF.forward()
    LR.forward()

def bw():
    RF.backward()
    RR.backward()
    LF.backward()
    LR.backward()
    
def right():
    RF.backward()
    RR.backward()
    LF.forward()
    LR.forward()

def left():
    RF.forward()
    RR.forward()
    LF.backward()
    LR.backward()

def stop():
    RF.stop()
    RR.stop()
    LF.stop()
    LR.stop()

# Defining the Pygame window, and adding the functions to keypresses
# For example: W - fw() (forward)

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

# When the script is stopped, stop everything down
try:
    while is_running:
        sleep(0.001)
finally:
    stop()
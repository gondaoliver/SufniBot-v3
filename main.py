import RPi.GPIO as GPIO
import time 
import pygame

GPIO.setmode(GPIO.BCM)

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

GPIO.setup(RFF, GPIO.OUT)
GPIO.setup(RFB, GPIO.OUT)
GPIO.setup(LFF, GPIO.OUT)
GPIO.setup(LFB, GPIO.OUT) 
GPIO.setup(RRF, GPIO.OUT)
GPIO.setup(RRB, GPIO.OUT)
GPIO.setup(LRF, GPIO.OUT)
GPIO.setup(LRB, GPIO.OUT)

# Making functions for commands
# For example: Forward: RFF,LFF,RRF,LRF - HIGH

def fw():
    GPIO.output(RFF, GPIO.HIGH)
    GPIO.output(LFF, GPIO.HIGH)
    GPIO.output(RRF, GPIO.HIGH)
    GPIO.output(LRF, GPIO.HIGH)

def bw():
    GPIO.output(RFB, GPIO.HIGH)
    GPIO.output(LFB, GPIO.HIGH)
    GPIO.output(RRB, GPIO.HIGH)
    GPIO.output(LRB, GPIO.HIGH)

def right():
    GPIO.output(LFF, GPIO.HIGH)
    GPIO.output(LRF, GPIO.HIGH)
    GPIO.output(RFB, GPIO.HIGH)
    GPIO.output(RRB, GPIO.HIGH)

def left():
    GPIO.output(LFB, GPIO.HIGH)
    GPIO.output(LRB, GPIO.HIGH)
    GPIO.output(RFF, GPIO.HIGH)
    GPIO.output(RRF, GPIO.HIGH)

def stop():
    GPIO.output(RFF, GPIO.LOW)
    GPIO.output(LFF, GPIO.LOW)
    GPIO.output(RRF, GPIO.LOW)
    GPIO.output(LRF, GPIO.LOW)
    GPIO.output(RFB, GPIO.LOW)
    GPIO.output(LFB, GPIO.LOW)
    GPIO.output(RRB, GPIO.LOW)
    GPIO.output(LRB, GPIO.LOW)

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
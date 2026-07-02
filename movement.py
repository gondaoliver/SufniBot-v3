from platform_utils import IS_RPI

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

if IS_RPI:
    from gpiozero import Motor

    RF = Motor(RFF, RFB)
    RR = Motor(RRF, RRB)
    LF = Motor(LFF, LFB)
    LR = Motor(LRF, LRB)
else:
    print("[movement] Not running on a Raspberry Pi - gpiozero disabled, using no-op motors.")

    class _DummyMotor:
        def forward(self, speed=1):
            pass

        def backward(self, speed=1):
            pass

        def stop(self):
            pass

    RF = _DummyMotor()
    RR = _DummyMotor()
    LF = _DummyMotor()
    LR = _DummyMotor()

# Making functions for commands
# For example: Forward: RFF,LFF,RRF,LRF - HIGH

def fw(pwmspeed):
    RF.forward(speed=pwmspeed)
    RR.forward(speed=pwmspeed)
    LF.forward(speed=pwmspeed)
    LR.forward(speed=pwmspeed)

def bw(pwmspeed):
    RF.backward(speed=pwmspeed)
    RR.backward(speed=pwmspeed)
    LF.backward(speed=pwmspeed)
    LR.backward(speed=pwmspeed)

def right(pwmspeed):
    RF.backward(speed=pwmspeed)
    RR.backward(speed=pwmspeed)
    LF.forward(speed=pwmspeed)
    LR.forward(speed=pwmspeed)

def left(pwmspeed):
    RF.forward(speed=pwmspeed)
    RR.forward(speed=pwmspeed)
    LF.backward(speed=pwmspeed)
    LR.backward(speed=pwmspeed)

def stop():
    RF.stop()
    RR.stop()
    LF.stop()
    LR.stop()

def autohold():
    RF.forward(speed=0.1)
    RR.forward(speed=0.1)
    LF.forward(speed=0.1)
    LR.forward(speed=0.1)

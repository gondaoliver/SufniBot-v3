from platform_utils import IS_RPI

SERVO_CHANNELS = {
    "base": 0,
    "neck": 5,
    "gripper": 8,
    "tail": 7,
}

if IS_RPI:
    from adafruit_servokit import ServoKit

    kit = ServoKit(channels=16)
else:
    print("[servo] Not running on a Raspberry Pi - adafruit_servokit disabled, using no-op servos.")

    class _DummyServo:
        angle = None

    class _DummyKit:
        def __init__(self):
            self.servo = [_DummyServo() for _ in range(16)]

    kit = _DummyKit()

def moveAngle(current_angle, direction, servo_name="base"):
    if servo_name == "tail":
        new_angle = current_angle + (10 if direction == "positive" else -10)
        new_angle = max(0, min(180, new_angle))
        kit.servo[SERVO_CHANNELS[servo_name]].angle = new_angle
    else:
        new_angle = current_angle + (5 if direction == "positive" else -5)
        new_angle = max(0, min(180, new_angle))
        kit.servo[SERVO_CHANNELS[servo_name]].angle = new_angle
    return new_angle

def setAngle(servo_name, angle):
    kit.servo[SERVO_CHANNELS[servo_name]].angle = angle
    return angle

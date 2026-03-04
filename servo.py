from adafruit_servokit import ServoKit

kit = ServoKit(channels=16)

SERVO_CHANNELS = {
    "base": 0,
    "neck": 1,
    "gripper": 2,
    "tail": 5,
}

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
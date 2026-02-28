def moveAngle(servo, direction):
    if direction == "positive":
        servo = servo+1
    else:
        servo = servo-1
    return servo

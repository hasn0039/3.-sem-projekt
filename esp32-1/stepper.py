from machine import Pin
import time

class Stepper:
    """Stepper motor controller for 28BYJ-48 with ULN2003 driver"""
    FULL_ROTATION = int(4075.7728395061727 / 8)

    HALF_STEP = [
        [0, 0, 0, 1],
        [0, 0, 1, 1],
        [0, 0, 1, 0],
        [0, 1, 1, 0],
        [0, 1, 0, 0],
        [1, 1, 0, 0],
        [1, 0, 0, 0],
        [1, 0, 0, 1],
    ]

    FULL_STEP = [
        [1, 0, 1, 0],
        [0, 1, 1, 0],
        [0, 1, 0, 1],
        [1, 0, 0, 1]
    ]
    
    def __init__(self, pin1, pin2, pin3, pin4, delay, mode=1):
        if mode == 1:
            self.mode = self.FULL_STEP
        elif mode == 0:
            self.mode = self.HALF_STEP
        else:
            raise ValueError("Mode must be either 0 or 1")
        
        self.pin1 = Pin(pin1, Pin.OUT)
        self.pin2 = Pin(pin2, Pin.OUT)
        self.pin3 = Pin(pin3, Pin.OUT)
        self.pin4 = Pin(pin4, Pin.OUT)
        self.delay = delay  # Recommend 10+ for FULL_STEP, 1 is OK for HALF_STEP
        
        self.reset()
        
    def step(self, count, direction=1):
        """Rotate count steps. direction = -1 means backwards"""
        if count < 0:
            direction = -1
            count = -count
        for x in range(count):
            for bit in self.mode[::direction]:
                self.pin1(bit[0])
                self.pin2(bit[1])
                self.pin3(bit[2])
                self.pin4(bit[3])
                time.sleep_ms(self.delay)
        self.reset()
    
    def angle(self, r, direction=1):
        """Rotate by angle (degrees)"""
        self.step(int(self.FULL_ROTATION * r / 360), direction)
    
    def reset(self):
        """Reset all pins to 0"""
        self.pin1(0) 
        self.pin2(0) 
        self.pin3(0) 
        self.pin4(0)

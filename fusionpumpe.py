from stepper import Stepper
from machine import Pin
from time import sleep
# Initiation of Pins
In1 = Pin(16, Pin.OUT)
In2 = Pin(17, Pin.OUT)
In3 = Pin(5, Pin.OUT)
In4 = Pin(18, Pin.OUT)

# 1 omgang rundt = 509 steps = 3 ml
# 1 ml = 182 steps

#create stepper object. This is running in half steps
s1 = Stepper(In1, In2, In3, In4, delay = 1, mode=0)
s1.step(2000)
sleep(1)
s1.step(-1900)

#s1.step(18)        # forward 0.1 ml
#s1.step(18, -1)    # backwards 0.1 ml
#s1.step(1820)      # pushing 10 ml
#s1.step(1820, -1)  # sucking 10 ml
#s1.angle(360)      # pushing 3 ml
#s1.angle(-360)     # sucking 3 ml"""

#kode til tempratursensor
import machine, onewire, ds18x20, time

ds_pin = machine.Pin(4)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))

roms = ds_sensor.scan()
print('Found DS devices: ', roms)

while True:
  ds_sensor.convert_temp()
  time.sleep_ms(750)
  for rom in roms:
    print(rom)
    print(ds_sensor.read_temp(rom))
  time.sleep(5)

#photo-resistor kode. når value er er høj er der mørk og lav er der lys

from machine import ADC, Pin
import time

ldr = ADC(Pin(32))   # or 32/33/35/36/39
ldr.atten(ADC.ATTN_11DB)  # full range 0–3.3V
ldr.width(ADC.WIDTH_12BIT)

while True:
    value = ldr.read()  # 0–4095
    print("LDR value:", value)
    time.sleep(0.2)

#laser kode med LDR modul
#kode kode virker men skal har en bedre fysisk opsætnint
#samt find ud af hvordan vi kan få LDR til at virke korrekt

from machine import ADC, Pin
import time

# LDR på S-pin → GPIO34
ldr = ADC(Pin(34))
ldr.atten(ADC.ATTN_11DB)
ldr.width(ADC.WIDTH_12BIT)

# Laser S-pin → GPIO15
laser = Pin(32, Pin.OUT)
laser.on()       # Tænd laser

THRESHOLD = 4000   # Juster efter dine målinger

while True:
    value = ldr.read()

    if value > THRESHOLD:
        print("Stråle brudt! Værdi:", value)
    else:
        print("OK:", value)

    time.sleep(0.1)


#koden nedenfor er lib til steppper

import time
from machine import Pin

# only test for uln2003
class Stepper:
    FULL_ROTATION = int(4075.7728395061727 / 8) # http://www.jangeox.be/2013/10/stepper-motor-28byj-48_25.html

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
        
        # Initialize all to 0
        self.reset()
        
    def step(self, count, direction=1):
        #Rotate count steps. direction = -1 means backwards
        if count<0:
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
        self.step(int(self.FULL_ROTATION * r / 360), direction)
    def reset(self):
        # Reset to 0, no holding, these are geared, you can't move them
        self.pin1(0) 
        self.pin2(0) 
        self.pin3(0) 
        self.pin4(0)
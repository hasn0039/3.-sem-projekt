import time
import machine
from machine import Pin, ADC
import onewire
import ds18x20

class TemperatureSensor:
    """DS18X20 One-Wire Temperature Sensor"""
    def __init__(self, pin):
        ds_pin = machine.Pin(pin)
        self.ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
        self.roms = self.ds_sensor.scan()
        print('Found DS devices: ', self.roms)
    
    def read_all(self):
        """Read temperature from all sensors"""
        self.ds_sensor.convert_temp()
        time.sleep_ms(750)
        temperatures = {}
        for rom in self.roms:
            temperatures[str(rom)] = self.ds_sensor.read_temp(rom)
        return temperatures


class PhotoResistor:
    """LDR (Light Dependent Resistor) Sensor"""
    def __init__(self, pin):
        self.ldr = ADC(Pin(pin))
        self.ldr.atten(ADC.ATTN_11DB)  # full range 0–3.3V
        self.ldr.width(ADC.WIDTH_12BIT)
    
    def read(self):
        """Read LDR value (0-4095). High = dark, Low = bright"""
        return self.ldr.read()


class LaserModule:
    """Laser with LDR break-beam detector"""
    def __init__(self, laser_pin, ldr_pin, threshold=4000):
        self.laser = Pin(laser_pin, Pin.OUT)
        self.ldr = ADC(Pin(ldr_pin))
        self.ldr.atten(ADC.ATTN_11DB)
        self.ldr.width(ADC.WIDTH_12BIT)
        self.threshold = threshold
    
    def laser_on(self):
        """Turn on laser"""
        self.laser.on()
    
    def laser_off(self):
        """Turn off laser"""
        self.laser.off()
    
    def is_beam_broken(self):
        """Check if laser beam is broken"""
        value = self.ldr.read()
        return value > self.threshold


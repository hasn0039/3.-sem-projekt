"""
Consolidated Raspberry Pi Project
Controls: Stepper Motor, Temperature Sensor, Photo Resistor (LDR), and Laser
Integrates with Node-RED dashboard for liquid displacement control
"""

import machine
import onewire
import ds18x20
import time
import json
from machine import Pin, ADC
from umqtt.simple import MQTTClient

# =============================================================================
# STEPPER MOTOR CLASS
# =============================================================================

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


# =============================================================================
# SENSOR CLASSES
# =============================================================================

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

# =============================================================================
# MAIN PROGRAM
# =============================================================================

# MQTT Configuration
MQTT_BROKER = "localhost"  # Change to your MQTT broker IP
MQTT_CLIENT_ID = "rasp_liquid_system"
MQTT_TOPIC_COMMAND = "liquid_system/command"
MQTT_TOPIC_STATUS = "liquid_system/status"
MQTT_TOPIC_LEVEL = "liquid_system/level"
MQTT_TOPIC_TEMP = "liquid_system/temperature"

# Stepper calibration
# 1 rotation = 509 steps = 3 ml
# 1 ml = ~170 steps (509/3)
STEPS_PER_ML = 170


class LiquidDispensationSystem:
    """Main system controller integrating all components with Node-RED"""
    
    def __init__(self, mqtt_broker, client_id):
        self.mqtt_broker = mqtt_broker
        self.client_id = client_id
        self.client = None
        self.stepper = None
        self.temp_sensor = None
        self.photo_resistor = None
        self.laser = None
        self.current_level = 0
        self.is_running = False
        
    def init_components(self):
        """Initialize all hardware components"""
        try:
            print("\n" + "=" * 60)
            print("Initializing Liquid Dispensation System")
            print("=" * 60)
            
            # Initialize Stepper Motor
            print("Initializing Stepper Motor...")
            In1 = Pin(16, Pin.OUT)
            In2 = Pin(17, Pin.OUT)
            In3 = Pin(5, Pin.OUT)
            In4 = Pin(18, Pin.OUT)
            self.stepper = Stepper(In1, In2, In3, In4, delay=1, mode=0)
            print("✓ Stepper Motor initialized")
            
            # Initialize Temperature Sensor
            print("Initializing Temperature Sensor...")
            self.temp_sensor = TemperatureSensor(pin=4)
            print("✓ Temperature Sensor initialized")
            
            # Initialize Photo Resistor (water level sensor)
            print("Initializing Photo Resistor (Level Sensor)...")
            self.photo_resistor = PhotoResistor(pin=32)
            print("✓ Photo Resistor initialized")
            
            # Initialize Laser Module (break-beam detector)
            print("Initializing Laser Module...")
            self.laser = LaserModule(laser_pin=15, ldr_pin=34, threshold=4000)
            self.laser.laser_on()
            print("✓ Laser Module initialized")
            
            print("\nAll components initialized successfully!\n")
            return True
            
        except Exception as e:
            print(f"ERROR during initialization: {e}")
            return False
    
    def connect_mqtt(self):
        """Connect to MQTT broker"""
        try:
            print(f"Connecting to MQTT broker at {self.mqtt_broker}...")
            self.client = MQTTClient(self.client_id, self.mqtt_broker)
            self.client.set_callback(self.mqtt_callback)
            self.client.connect()
            self.client.subscribe(MQTT_TOPIC_COMMAND)
            print("✓ Connected to MQTT broker")
            return True
        except Exception as e:
            print(f"ERROR: Failed to connect to MQTT: {e}")
            print("Running in standalone mode (no Node-RED control)")
            return False
    
    def mqtt_callback(self, topic, msg):
        """Handle incoming MQTT messages from Node-RED"""
        try:
            message = msg.decode('utf-8')
            print(f"Received command: {message} on topic: {topic}")
            
            # Parse JSON command
            try:
                cmd = json.loads(message)
                ml_amount = float(cmd.get('ml', 0))
                direction = int(cmd.get('direction', 1))  # 1=push, -1=pull
                
                if ml_amount > 0:
                    self.dispense_liquid(ml_amount, direction)
                else:
                    print("Invalid ml amount")
                    
            except json.JSONDecodeError:
                # Try simple number format
                try:
                    ml_amount = float(message)
                    self.dispense_liquid(ml_amount, direction=1)
                except ValueError:
                    print(f"Could not parse command: {message}")
                    
        except Exception as e:
            print(f"ERROR in callback: {e}")
    
    def dispense_liquid(self, ml_amount, direction=1):
        """
        Dispense specified amount of liquid
        direction: 1 = push (dispense), -1 = pull (draw)
        """
        if self.is_running:
            print("⚠️  System already running, please wait...")
            return
        
        self.is_running = True
        steps = int(ml_amount * STEPS_PER_ML)
        
        print(f"\n{'='*60}")
        print(f"Dispensing {ml_amount} ml ({steps} steps)...")
        print(f"Direction: {'PUSH (dispense)' if direction > 0 else 'PULL (draw)'}")
        print(f"{'='*60}\n")
        
        try:
            # Record initial water level
            initial_level = self.photo_resistor.read()
            print(f"Initial water level: {initial_level}")
            
            # Run stepper
            if direction > 0:
                self.stepper.step(steps, direction=1)
            else:
                self.stepper.step(steps, direction=-1)
            
            time.sleep(1)
            
            # Record final water level
            final_level = self.photo_resistor.read()
            displacement = final_level - initial_level
            print(f"Final water level: {final_level}")
            print(f"Water level change: {displacement}")
            
            # Publish results to Node-RED
            self.publish_status(ml_amount, initial_level, final_level, displacement)
            
        except Exception as e:
            print(f"ERROR during dispensing: {e}")
        finally:
            self.is_running = False
            print("✓ Dispensing complete\n")
    
    def read_sensors(self):
        """Read all sensors and return data"""
        data = {}
        
        try:
            # Temperature
            temps = self.temp_sensor.read_all()
            data['temperature'] = temps
            
            # Water level (photoresistor)
            data['water_level'] = self.photo_resistor.read()
            
            # Laser beam status
            data['laser_beam_broken'] = self.laser.is_beam_broken()
            
            return data
        except Exception as e:
            print(f"ERROR reading sensors: {e}")
            return None
    
    def publish_status(self, ml_dispensed, level_before, level_after, displacement):
        """Publish system status to Node-RED"""
        if not self.client:
            return
        
        try:
            status = {
                'ml_dispensed': ml_dispensed,
                'level_before': level_before,
                'level_after': level_after,
                'displacement': displacement,
                'timestamp': time.time()
            }
            self.client.publish(MQTT_TOPIC_STATUS, json.dumps(status))
        except Exception as e:
            print(f"ERROR publishing status: {e}")
    
    def publish_sensor_data(self):
        """Continuously publish sensor data to Node-RED"""
        if not self.client:
            return
        
        try:
            data = self.read_sensors()
            if data:
                # Publish water level
                self.client.publish(MQTT_TOPIC_LEVEL, str(data['water_level']))
                
                # Publish temperature
                if data['temperature']:
                    temp_str = json.dumps(data['temperature'])
                    self.client.publish(MQTT_TOPIC_TEMP, temp_str)
        except Exception as e:
            print(f"ERROR publishing sensor data: {e}")
    
    def run(self):
        """Main event loop"""
        print("\nStarting main event loop...")
        
        mqtt_connected = self.connect_mqtt()
        iteration = 0
        
        try:
            while True:
                iteration += 1
                
                # Check MQTT messages
                if mqtt_connected:
                    try:
                        self.client.check_msg()
                    except Exception as e:
                        print(f"MQTT check error: {e}")
                
                # Periodically publish sensor data
                if iteration % 5 == 0:
                    print(f"\n--- Reading #{iteration // 5} ---")
                    data = self.read_sensors()
                    if data:
                        print(f"Water Level: {data['water_level']}")
                        print(f"Temperature: {data['temperature']}")
                        print(f"Laser Beam: {'BROKEN ⚠️' if data['laser_beam_broken'] else 'OK ✓'}")
                    
                    self.publish_sensor_data()
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\nProgram interrupted by user")
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown of all components"""
        print("Shutting down system...")
        
        # Reset stepper
        if self.stepper:
            self.stepper.reset()
        
        # Turn off laser
        if self.laser:
            self.laser.laser_off()
        
        # Disconnect MQTT
        if self.client:
            try:
                self.client.disconnect()
            except:
                pass
        
        print("All components reset. Goodbye!")


def main():
    """Main entry point"""
    system = LiquidDispensationSystem(MQTT_BROKER, MQTT_CLIENT_ID)
    
    # Initialize hardware
    if not system.init_components():
        print("ERROR: Failed to initialize components")
        return
    
    # Run main loop
    system.run()


# Example usage of individual components (commented out):
"""
# Stepper Motor Examples:
# s1.step(18)        # forward 0.1 ml
# s1.step(18, -1)    # backwards 0.1 ml
# s1.step(1820)      # pushing 10 ml
# s1.step(1820, -1)  # sucking 10 ml
# s1.angle(360)      # pushing 3 ml
# s1.angle(-360)     # sucking 3 ml
"""


if __name__ == "__main__":
    main()

import json
from machine import Pin, ADC
from umqtt.simple import MQTTClient
import espnow

# MQTT Configuration



class LiquidDispensationSystem:
    
    
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
            in1 = Pin(16, Pin.OUT)
            in2 = Pin(17, Pin.OUT)
            in3 = Pin(5, Pin.OUT)
            in4 = Pin(18, Pin.OUT)
            self.stepper = Stepper(in1, in2, in3, in4, delay=1, mode=0)
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
        """Continuously publish sensor data to flask"""
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


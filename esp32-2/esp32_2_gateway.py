import network
import espnow
import time
import ubinascii
import json
from umqtt.simple import MQTTClient


# Wi-Fi til Raspberry Pi

SSID = "ekgruppe7pi"
PASSWORD = "cisco123"

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

while not wlan.isconnected():
    time.sleep(1)

print("ESP32-2 forbundet til Wi-Fi")
print("IP:", wlan.ifconfig())


# ESP-NOW init

esp = espnow.ESPNow()
esp.active(True)

# MAC på ESP32-1 (SKAL rettes)
ESP32_1_MAC = b'\x24\x6F\x28\xAA\xBB\xCC'
esp.add_peer(ESP32_1_MAC)

print("ESP-NOW aktiv (ESP32-2)")
print("ESP32-1 peer:", ubinascii.hexlify(ESP32_1_MAC, ":").decode())


# MQTT config (Pi)

MQTT_BROKER = "192.168.1.10"   # Raspberry Pi IP
CLIENT_ID = "esp32_gateway"

TOPIC_SENSOR = b"esp32/sensors"
TOPIC_COMMAND = b"esp32/command"

mqtt = MQTTClient(CLIENT_ID, MQTT_BROKER)

def mqtt_callback(topic, msg):
    try:
        message = msg.decode()
        print("MQTT kommando:", message)

        # REGEX-VALIDERING
        # Tillad fx: "DISPENSE: "10" eller "25"
        if not re.match(r"^(DISPENSE:\d+|\d+)$", message):
            print("Ugyldigt kommandoformat – afvist")
            return

        # Send kun gyldige kommandoer videre til ESP32-1
        esp.send(ESP32_1_MAC, message)

    except Exception as e:
        print("Fejl i MQTT callback:", e)

mqtt.set_callback(mqtt_callback)
mqtt.connect()
mqtt.subscribe(TOPIC_COMMAND)

print("MQTT forbundet til Raspberry Pi")

# Main loop

while True:
    # Tjek MQTT (kommandoer fra Pi)
    mqtt.check_msg()

    # Tjek ESP-NOW (data fra ESP32-1)
    host, msg = esp.recv()
    if msg:
        try:
            print("ESP-NOW data:", msg)
            mqtt.publish(TOPIC_SENSOR, msg)
        except Exception as e:
            print("MQTT send fejl:", e)

    time.sleep(0.2)

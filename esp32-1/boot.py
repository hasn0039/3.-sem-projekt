# boot.py
import network
import espnow
import ubinascii
import esp
import gc

esp.osdebug(None)
gc.collect()

sta = network.Wlan(network.STA_IF)
sta.active(True)
sta.disconnect()

sta.config(pm=sta.PM_NONE)

esp_now = espnow.ESPNow()
esp_now.active(True)

print("ESP32-1 ESP-NOW aktiv")
print("ESP32-1 MAC:", ubinascii.hexlify(sta.config("mac"), ":").decode())
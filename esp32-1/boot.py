# boot.py
import network
import esp
import gc
import network
import espnow


esp.osdebug(None)
gc.collect()

SSID = "ekgruppe7pi"
PASSWORD = "cisco123"


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        wlan.connect(SSID, PASSWORD)
        for _ in range(30):
            if wlan.isconnected():
                break

    return wlan.isconnected()


connect_wifi()


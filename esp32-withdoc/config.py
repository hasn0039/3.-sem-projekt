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
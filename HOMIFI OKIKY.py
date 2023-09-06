import serial
# import pynmea2
import time
import requests 
import RPI.GPIO as GPIO
import threading
import paho.mqtt.client as mqtt

distance = 0.0

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

latitude = -6.902494
longitude = 107.537933

get_latitude = 0.000
get_longitude = 0.000

threshold = 50

BUZZER_STATUS = False

TOKEN = "BBFF-nJ1zEZ8G0FNge3KjytpCCigcmaIGIP"
DEVICE_LABEL = "Project"
LED_RED = 10
LED_GREEN = 11
LED_WHITE = 9

LED_RED_STATUS = True
LED_GREEN_STATUS = False
LED_WHITE_STATUS = False

BUTTON1 = 17 #red
BUTTON2 = 27 #white
BUTTON3 = 22 #green

BUZZER = 5 

GPIO.setup(BUZZER,GPIO.OUT)
GPIO.output(BUZZER,GPIO.LOW)

GPIO.setup(LED_RED,GPIO.OUT)
GPIO.setup(LED_GREEN,GPIO.OUT)
GPIO.setup(LED_WHITE,GPIO.OUT)

GPIO.out(LED_RED,GPIO.LOW)
GPIO.out(LED_GREEN,GPIO.LOW)
GPIO.out(LED_WHITE,GPIO.LOW)

GPIO.setup(BUTTON1,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(BUTTON2,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(BUTTON3,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)

def haversine(lat1, lon1, lat2, lon2):
    # Radius of the Earth in meters
    radius = 6371000.0

    # Convert latitude and longitude from degrees to radians
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Calculate the distance in meters
    distance = radius * c

    return distance

def kirim_data(payload):
    print(payload)
    url = "http://industrial.api.ubidots.com"
    url = "{}/api/v1.6/devices/{}".format(url,DEVICE_LABEL)
    headers = {"X-Auth-Token":TOKEN,"Content-Type":"application/json"}
    status = 400
    attempts = 0
    while status >= 400 and attempts<=5:
        req = requests.post(url=url,headers=headers,json=payload)
        status = req.status_code
        attempts +=1
        time.sleep(1)
    
    print(req.status_code, req.json())
    
    if status>=400:
        print("Error")
        return False
    print("berhasil")
    return True


def on_message(client, userdata, message):
    global get_latitude
    global get_longitude
    get_latitude = message.payload.decode().split(",")[0]
    get_longitude = message.payload.decode().split(",")[1]
    # print(f"Received message on topic '{message.topic}': {message.payload.decode()}")

def loop_mqtt():
    client = mqtt.Client()

    # Set the callback function for message reception
    client.on_message = on_message

    # Connect to the MQTT broker (replace with your broker's information)
    broker_address = "test.mosquitto.org"
    broker_port = 1883  # Default MQTT port
    client.connect(broker_address, broker_port)

    # Subscribe to a topic
    topic = "/skilvul/location_149"
    client.subscribe(topic)

    # Start the MQTT loop to listen for incoming messages
    client.loop_forever()

def loop_buzzer():
    while True:
        if BUZZER_STATUS:
            GPIO.output(BUZZER,GPIO.HIGH)
            time.sleep(0.5)
            GPIO.output(BUZZER,GPIO.LOW)
            time.sleep(0.5)
        else:
            GPIO.output(BUZZER,GPIO.LOW)

def loop_logic():
    global LED_RED_STATUS
    global LED_GREEN_STATUS
    global LED_WHITE_STATUS
    global distance
    try:
        while True:
            # Read data from the GPS module
            
            BUTTON1_STATUS = GPIO.input(BUTTON1)
            BUTTON2_STATUS = GPIO.input(BUTTON2)
            BUTTON3_STATUS = GPIO.input(BUTTON3)

            if BUTTON1_STATUS == GPIO.HIGH:
                LED_RED_STATUS = True
                LED_WHITE_STATUS = False
                LED_GREEN_STATUS = False
                time.sleep(0.2)
            
            if BUTTON2_STATUS == GPIO.HIGH:
                LED_RED_STATUS = False
                LED_WHITE_STATUS = True
                LED_GREEN_STATUS = False
                time.sleep(0.2)
            
            if BUTTON3_STATUS == GPIO.HIGH:
                LED_RED_STATUS = False
                LED_WHITE_STATUS = False
                LED_GREEN_STATUS = True
                time.sleep(0.2)

            GPIO.output(LED_RED,LED_RED_STATUS)
            GPIO.output(LED_GREEN,LED_GREEN_STATUS)
            GPIO.output(LED_BLUE,LED_BLUE_STATUS)
            distance = haversine(latitude,longitude,get_latitude,get_longitude)
            if distance <= threshold and LED_RED_STATUS == False and LED_WHITE_STATUS == True and LED_GREEN_STATUS == False:
                BUZZER_STATUS = True
            else:
                BUZZER_STATUS = False
                
            
    except KeyboardInterrupt:
        print("Program terminated by user")

def loop_send():
    while True:
        payload = {'home':{"value":1,"context":{"lat":latitude,"lng":longitude}},
        "delivery":{"value":1,"context":{"lat":get_latitude,"lng":get_longitude}}, 
        "distance":distance,"status_ready":int(LED_WHITE_STATUS),
        "status_not_ready":int(LED_RED_STATUS),"status_working":int(LED_GREEN_STATUS)}
        kirim = kirim_data(payload)
        time.sleep(5)

if __name__ == "__main__":
    try:
        threading.Thread(target=loop_mqtt).start()
        threading.Thread(target=loop_buzzer).start()
        threading.Thread(target=loop_logic).start()
        threading.Thread(target=loop_send).start()
    except KeyboardInterrupt:
        print("Program terminated by user")
import network
from umqtt.simple import MQTTClient
import random
import time

SSID = ""
PSSWD = ""

IP_BROKER = "192.168.0.7"

def connect_network():
    wlan = network.WLAN(network.WLAN.IF_STA)
    wlan.active(True)
    if not wlan.isconnected():
        print("iniciando conexao com a rede...")
        wlan.connect(SSID, PSSWD)
        
        while not wlan.isconnected():
            pass
    print(f"configuracao de rede: {wlan.ipconfig('addr4')}")
    
def connect_MQTT():
    client = MQTTClient("esp32DHT11", IP_BROKER)
    client.connect()
    print("Conectado ao broker")
    return client

connect_network()
client = connect_MQTT()

while True:
    msg = random.randint(1, 10)
    print(f"Numero gerado: {msg}")
    client.publish(b"teste/espdth11", str(msg).encode())
    time.sleep(1)
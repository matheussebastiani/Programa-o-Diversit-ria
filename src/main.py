import dht
import machine
import time
import network
from umqtt.simple import MQTTClient

SSID = ""
PSSWD = ""

IP_BROKER = "192.168.0.7"

MQTT_CLIENT_ID = "esp32DHT11"

'''Cálculos'''
def calcular_media(leituras):
    if not leituras:
        return 0.0
    
    soma = sum(leituras)
    m = soma / len(leituras)
    return m

def calcular_desvio_padrao(leituras, media):
    if not leituras:
        return 0.0
    
    if media == 0.0:
        return 0.0
    
    soma_quadrados = 0.0
    
    for i in range(len(leituras)):
        soma_quadrados += (leituras[i] - media) ** 2
#        print(f"{leituras[i]}: ({leituras[i]} - {media} ** 2)")    
    
    s = (soma_quadrados / (len(leituras) - 1) ) ** 0.5
    return s
'''Cálculos'''

''' Rede '''
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
    client = MQTTClient(MQTT_CLIENT_ID, IP_BROKER)
    client.connect()
    print("Conectado ao broker")
    return client
''' Rede '''





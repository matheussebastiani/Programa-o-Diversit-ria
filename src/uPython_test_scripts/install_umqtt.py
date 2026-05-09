import mip
import network

'''
Necessário baixar o script em questão e executá-lo na ESP32 para que a biblioteca de MQTT seja instalado no interpretador Python que roda na ESP32
'''

SSID = "Greici"
PSSWD = "Greici20@"

def connect_network():
    wlan = network.WLAN(network.WLAN.IF_STA)
    wlan.active(True)
    if not wlan.isconnected():
        print("iniciando conexao com a rede...")
        wlan.connect(SSID, PSSWD)
        
        while not wlan.isconnected():
            pass
    print(f"configuracao de rede: {wlan.ipconfig('addr4')}")

connect_network()

mip.install("umqtt.simple")
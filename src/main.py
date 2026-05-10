import dht
import machine
import time
import network
from umqtt.simple import MQTTClient

SSID = "Greici"
PSSWD = "Greici20@"

IP_BROKER = "192.168.0.7"

MQTT_CLIENT_ID = "esp32DHT11"
TOPICO_MQTT = b"sensors/esp32_micropython"

''' DHT '''
PINO_DHT = machine.Pin(4)
''' DHT '''

checkpoint = 0

'''Cálculos'''
def calcular_media(leituras):
    if not leituras:
        return 0.0
    
    soma = sum(leituras)
    m = soma / len(leituras)
    return m

def calcular_desvio_padrao(leituras, media):
    
    print(leituras)
    print(media)
    
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

def main():
    
    connect_network()
    client = connect_MQTT()

    d = dht.DHT11(machine.Pin(4))
     
    global checkpoint
    while True:
        leituras = []
        for _ in range(0, 10):
            try:
                d.measure()
            
                leitura = d.temperature()
                print(leitura)
            
                if(leitura):
                    leituras.append(leitura)
            except Exception as e:
                print(f"Erro ao ler o sensor: {e}")
            
            time.sleep(1)
        
        media = calcular_media(leituras)
        s = calcular_desvio_padrao(leituras, media)
        
        print(f"Media: {media}, s: {s}")
        
        if media > 0:
            cv = (s / media) * 100 # Multiplica por 100 para vir em porcentagem
        else:
            cv = 1000
        
        if cv <= 10:
            valor_final = media
            checkpoint = valor_final
        
        elif checkpoint > 0 and cv > 10:
            valor_final = checkpoint
        
        else:
            valor_final = 0
        
        valor_final = valor_final * 100
        valor_final = int(valor_final)
        
        mensagem = str(valor_final)
        
        client.publish(TOPICO_MQTT, mensagem.encode("utf-8"))
        
        print(f"Mensagem enviada: {mensagem}")
        
if __name__ == "__main__":
    main()

# Exemplo de programa em Python efetuando a leitura de um sensor dht11
import dht
import machine
import time


d = dht.DHT11(machine.Pin(4))

while True:
    try:
        d.measure()
    
        temperatura = d.temperature()
        
        # Má notícia: o DHT11 pelo uPython não retorna um valor float, apenas um inteiro
        print(f"Temperatura: {temperatura}ºC")
        
        
        
    except Exception as e:
        print(f"Erro ao ler o DHT11: {e}")        
        
    time.sleep(1)
# Bibliotecas necessarias para o funcionamento do sensor e da rede
import dht
import machine
import time
import network
from umqtt.simple import MQTTClient
 
# -------------------------------------------------------------------
# Configuracoes gerais do sistema
# -------------------------------------------------------------------
 
# Dados da rede Wi-Fi
SSID  = "Greici"
PSSWD = "Greici20@"
 
# Endereco IP do computador que roda o broker MQTT
IP_BROKER = "192.168.0.7"
 
# Identificador unico deste cliente no broker
MQTT_CLIENT_ID = "esp32DHT11"
 
# Topico MQTT onde as temperaturas serao publicadas
TOPICO_MQTT = b"sensors/esp32_micropython"
 
# Tempo maximo em segundos aguardando conexao Wi-Fi antes de desistir
WIFI_TIMEOUT_S = 20
 
# Numero maximo de tentativas de conexao ao broker MQTT
MQTT_MAX_RETRIES = 5
 
# Tempo em segundos entre cada tentativa de conexao MQTT
MQTT_RETRY_DELAY_S = 3
 
# Numero maximo de tentativas de leitura do sensor por coleta
DHT_MAX_RETRIES = 3
 
# -------------------------------------------------------------------
# Configuracao do hardware
# -------------------------------------------------------------------
 
# Pino GPIO do ESP32 onde o pino DATA do sensor DHT esta conectado
PINO_DHT = machine.Pin(4)
 
# -------------------------------------------------------------------
# Variaveis de estado global
# -------------------------------------------------------------------
 
# Ultimo valor de temperatura considerado valido (usado quando CV esta alto)
checkpoint = 0.0
 
# Referencia global ao cliente MQTT, permite reconexao de qualquer funcao
client_mqtt = None
 
# -------------------------------------------------------------------
# Funcoes de calculo estatistico
# -------------------------------------------------------------------
 
def calcular_media(leituras):
    # Retorna 0 se a lista estiver vazia para evitar divisao por zero
    if not leituras:
        return 0.0
    return sum(leituras) / len(leituras)
 
 
def calcular_desvio_padrao(leituras, media):
    # Precisa de pelo menos 2 valores para calcular desvio padrao amostral
    if not leituras or media == 0.0 or len(leituras) < 2:
        return 0.0
 
    soma_quadrados = 0.0
    for i in range(len(leituras)):
        soma_quadrados += (leituras[i] - media) ** 2
#        print(f"{leituras[i]}: ({leituras[i]} - {media} ** 2)")
        
    s = (soma_quadrados / (len(leituras) - 1) ) ** 0.5
    
    return s
 
# -------------------------------------------------------------------
# Funcoes de conexao Wi-Fi
# -------------------------------------------------------------------
 
def connect_network():
    # Tenta conectar ao Wi-Fi e retorna True se conseguir, False se falhar
    try:
        # Inicializa a interface Wi-Fi no modo estacao (cliente)
        wlan = network.WLAN(network.WLAN.IF_STA)
        wlan.active(True)
 
        # Se ja estiver conectado, nao faz nada
        if wlan.isconnected():
            print(f"[WiFi] Ja conectado: {wlan.ipconfig('addr4')}")
            return True
 
        print(f"[WiFi] Conectando a '{SSID}'", end="")
        wlan.connect(SSID, PSSWD)
 
        # Aguarda a conexao com limite de tempo definido em WIFI_TIMEOUT_S
        tempo_espera = 0
        while not wlan.isconnected():
            if tempo_espera >= WIFI_TIMEOUT_S:
                # Tempo esgotado, rede nao disponivel
                print(f"\n[WiFi] Timeout apos {WIFI_TIMEOUT_S}s. Rede indisponivel.")
                return False
            time.sleep(1)
            tempo_espera += 1
            print(".", end="")
 
        print(f"\n[WiFi] Conectado! IP: {wlan.ipconfig('addr4')}")
        return True
 
    except Exception as e:
        # Captura qualquer erro inesperado durante a conexao
        print(f"\n[WiFi] Erro inesperado na conexao: {e}")
        return False
 
 
def wifi_esta_conectado():
    # Verifica se o Wi-Fi ainda esta ativo, sem lancar excecao
    try:
        wlan = network.WLAN(network.WLAN.IF_STA)
        return wlan.isconnected()
    except Exception:
        # Se nao foi possivel verificar, assume que esta desconectado
        return False
 
# -------------------------------------------------------------------
# Funcoes de conexao MQTT
# -------------------------------------------------------------------
 
def connect_MQTT():
    # Tenta conectar ao broker MQTT, repetindo ate MQTT_MAX_RETRIES vezes
    # Retorna o objeto cliente se conectar, ou None se todas as tentativas falharem
    for tentativa in range(1, MQTT_MAX_RETRIES + 1):
        try:
            print(f"[MQTT] Tentativa {tentativa}/{MQTT_MAX_RETRIES}...")
            c = MQTTClient(MQTT_CLIENT_ID, IP_BROKER)
            c.connect()
            print(f"[MQTT] Conectado ao broker {IP_BROKER}")
            return c  # retorna o cliente pronto para uso
 
        except OSError as e:
            # Erro de rede, como broker fora do ar ou IP errado
            print(f"[MQTT] OSError na tentativa {tentativa}: {e}")
 
        except Exception as e:
            # Qualquer outro erro inesperado
            print(f"[MQTT] Erro inesperado na tentativa {tentativa}: {e}")
 
        # Aguarda antes de tentar novamente, exceto na ultima tentativa
        if tentativa < MQTT_MAX_RETRIES:
            print(f"[MQTT] Aguardando {MQTT_RETRY_DELAY_S}s antes de nova tentativa...")
            time.sleep(MQTT_RETRY_DELAY_S)
 
    print("[MQTT] Todas as tentativas de conexao falharam.")
    return None
 
 
def publicar_com_reconexao(client, topico, mensagem):
    # Tenta publicar a mensagem. Se falhar, tenta reconectar e publicar de novo.
    # Retorna o cliente MQTT atual (pode ser um novo apos reconexao).
    try:
        client.publish(topico, mensagem)
        return client  # publicacao bem-sucedida, retorna o mesmo cliente
 
    except Exception as e:
        # A publicacao falhou, provavelmente a conexao caiu
        print(f"[MQTT] Falha ao publicar: {e}. Tentando reconectar...")
 
    # Verifica se o Wi-Fi ainda esta ativo antes de tentar o MQTT
    if not wifi_esta_conectado():
        print("[WiFi] Conexao perdida. Reconectando...")
        if not connect_network():
            # Wi-Fi nao voltou, nao ha o que fazer agora
            print("[WiFi] Reconexao falhou. Mensagem nao enviada.")
            return client  # retorna o cliente antigo, o proximo ciclo tentara novamente
 
    # Tenta reconectar ao broker MQTT
    novo_client = connect_MQTT()
    if novo_client is None:
        print("[MQTT] Reconexao MQTT falhou. Mensagem nao enviada.")
        return client  # idem: o proximo ciclo tentara novamente
 
    # Tenta publicar novamente com o novo cliente
    try:
        novo_client.publish(topico, mensagem)
        print("[MQTT] Reconectado e mensagem enviada com sucesso.")
        return novo_client  # retorna o novo cliente para os proximos ciclos
 
    except Exception as e:
        # Mesmo apos reconexao, a publicacao falhou
        print(f"[MQTT] Falha mesmo apos reconexao: {e}")
        return novo_client
 
# -------------------------------------------------------------------
# Funcao de leitura do sensor DHT
# -------------------------------------------------------------------
 
def ler_temperatura(sensor_dht):
    # Tenta ler a temperatura do sensor ate DHT_MAX_RETRIES vezes
    # Retorna o valor em float se obtiver uma leitura valida, ou None se falhar
    for tentativa in range(1, DHT_MAX_RETRIES + 1):
        try:
            # Dispara a medicao no sensor
            sensor_dht.measure()
            temp = sensor_dht.temperature()
 
            # Verifica se o valor esta dentro do range fisico do sensor
            # DHT11: 0 a 50 graus | DHT22: -40 a 80 graus
            if -40.0 <= temp <= 80.0:
                return float(temp)
            else:
                # Valor fora do range esperado, provavelmente leitura corrompida
                print(f"[DHT] Leitura fora do range: {temp}C (tentativa {tentativa})")
 
        except Exception as e:
            # Erro de comunicacao com o sensor (cabo solto, sensor com defeito, etc.)
            print(f"[DHT] Erro na leitura (tentativa {tentativa}/{DHT_MAX_RETRIES}): {e}")
 
        # Aguarda 200ms antes de tentar novamente
        #time.sleep_ms(200)
 
    # Todas as tentativas falharam
    print("[DHT] Todas as tentativas de leitura falharam.")
    return None
 
# -------------------------------------------------------------------
# Funcao principal
# -------------------------------------------------------------------
 
def main():
    global checkpoint, client_mqtt
 
    # Tenta conectar ao Wi-Fi na inicializacao
    # Se nao conseguir, reinicia o ESP32 apos 10 segundos
    if not connect_network():
        print("[BOOT] Sem Wi-Fi. Reiniciando em 10s...")
        time.sleep(10)
        machine.reset()
 
    # Tenta conectar ao broker MQTT na inicializacao
    # Se nao conseguir, reinicia o ESP32 apos 10 segundos
    client_mqtt = connect_MQTT()
    if client_mqtt is None:
        print("[BOOT] Sem MQTT. Reiniciando em 10s...")
        time.sleep(10)
        machine.reset()
 
    # Inicializa o objeto do sensor DHT no pino definido
    # Trocar dht.DHT11 por dht.DHT22 caso o sensor seja o DHT22
    try:
        d = dht.DHT11(PINO_DHT)
    except Exception as e:
        print(f"[BOOT] Erro ao inicializar sensor DHT: {e}")
        time.sleep(10)
        machine.reset()
 
    print("\n[LOOP] Iniciando ciclos de medicao...\n")
 
    # Loop principal: executa indefinidamente
    while True:
 
        # Lista que acumula as leituras validas do ciclo atual
        leituras = []
 
        # Coleta 10 leituras com intervalo de 1 segundo entre cada uma
        # O ciclo completo demora aproximadamente 10 segundos
        for i in range(10):
            temp = ler_temperatura(d)
 
            if temp is not None:
                # Leitura valida: adiciona a lista
                leituras.append(temp)
                print(f"  Leitura {i+1}/10: {temp:.1f}C")
            else:
                # Leitura invalida: descarta e continua
                print(f"  Leitura {i+1}/10: descartada (falha no sensor)")
 
            time.sleep(0.5)
 
        # Verifica se alguma leitura valida foi coletada neste ciclo
        if not leituras:
            print("[CICLO] Nenhuma leitura valida neste ciclo.")
 
            if checkpoint > 0:
                # Usa o ultimo valor seguro registrado
                valor_final = checkpoint
                print(f"[CICLO] Usando checkpoint: {checkpoint:.2f}C")
            else:
                # Nao ha checkpoint disponivel, nao e possivel publicar
                print("[CICLO] Sem checkpoint disponivel. Pulando publicacao.")
                continue  # volta ao inicio do while para um novo ciclo
 
        else:
            # Calcula a media e o desvio padrao das leituras coletadas
            media = calcular_media(leituras)
            s     = calcular_desvio_padrao(leituras, media)
 
            # Calcula o coeficiente de variacao (CV) em porcentagem
            # CV alto indica que as leituras estao muito dispersas (sensor instavel)
            cv = (s / media) * 100 if media > 0 else 1000.0
 
            print(f"\n[CICLO] Leituras validas: {len(leituras)}/10")
            print(f"[CICLO] Media: {media:.2f}C | Desvio: {s:.2f} | CV: {cv:.2f}%")
 
            if cv <= 10:
                # CV dentro do limite: leituras confiaveis
                # Atualiza o checkpoint com o novo valor seguro
                valor_final = media
                checkpoint  = valor_final
                print(f"[CICLO] CV OK. Novo checkpoint: {checkpoint:.2f}C")
 
            elif checkpoint > 0:
                # CV acima do limite: leituras com muita variacao
                # Usa o checkpoint anterior como valor seguro
                valor_final = checkpoint
                print(f"[CICLO] CV alto ({cv:.2f}%). Usando checkpoint: {checkpoint:.2f}C")
 
            else:
                # CV alto e nenhum checkpoint disponivel ainda
                print(f"[CICLO] CV alto e sem checkpoint. Pulando publicacao.")
                continue  # volta ao inicio do while para um novo ciclo
 
        # Converte o valor para inteiro multiplicando por 100
        # Exemplo: 23.45 graus vira 2345 (o votador divide por 100 para recuperar)
        valor_inteiro = int(round(valor_final * 100))
 
        # Codifica como string de bytes para envio via MQTT
        mensagem = str(valor_inteiro).encode("utf-8")
 
        print(f"[MQTT] Publicando: {mensagem} ({valor_final:.2f}C)")
 
        # Publica com tratamento de reconexao automatica em caso de falha
        client_mqtt = publicar_com_reconexao(client_mqtt, TOPICO_MQTT, mensagem)
        print()
 
 
# Ponto de entrada do programa
if __name__ == "__main__":
    main()
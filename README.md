# TEMPTF — Controlador de Temperatura Tolerante a Falhas
## Nó: ESP32 + MicroPython + DHT22 + MQTT

---

## Histórico:

| DATA | AUTOR | DESCRIÇÃO     |
|--------|-------|------------|
| 19/04/2026  | Brenda, Gustavo e Matheus   | Configuração da IDE, micropython (UPYcraft), ESP 32 e pesquisa sobre as bibliotecas, códigos, estratégias e protocolo |

## Estrutura dos arquivos

```
temptf_dht22/
├── config.py         # ← EDITE AQUI: Wi-Fi, IP do broker, pino GPIO
├── network_utils.py  # Conexão Wi-Fi e MQTT com reconexão automática
├── stats.py          # Média, desvio padrão, CV, arredondamento científico
├── main.py           # Loop principal do sensor (upload para o ESP32)
└── voter.py          # Sistema votador para o PC (Python 3 + paho-mqtt)
```

---

## Configuração rápida

### 1. Edite `config.py`
```python
WIFI_SSID      = "nome_da_sua_rede"
WIFI_PASSWORD  = "senha"
MQTT_BROKER    = "192.168.X.X"   # IP do PC com o broker Mosquitto
DHT_PIN        = 4               # GPIO do ESP32 conectado ao DATA do DHT22
```

### 2. Instale o broker Mosquitto no PC
```bash
# Ubuntu/Debian
sudo apt install mosquitto mosquitto-clients
sudo systemctl start mosquitto

# Windows: baixar em https://mosquitto.org/download/
```

### 3. Upload para o ESP32 (MicroPython já gravado)
Use **Thonny**, **ampy** ou **mpremote**:
```bash
# Via ampy
pip install adafruit-ampy
ampy --port /dev/ttyUSB0 put config.py
ampy --port /dev/ttyUSB0 put network_utils.py
ampy --port /dev/ttyUSB0 put stats.py
ampy --port /dev/ttyUSB0 put main.py
```

### 4. Rode o votador no PC
```bash
pip install paho-mqtt
python voter.py
```

---

## Diagrama do sistema

```
┌─────────────────────────────────────────────────────────┐
│                    REDE LOCAL (Wi-Fi / LAN)             │
│                                                         │
│  ┌──────────────┐    MQTT     ┌─────────────────────┐  │
│  │ ESP32 + DHT22│──────────►  │                     │  │
│  │ (MicroPython)│             │   BROKER MQTT       │  │
│  └──────────────┘             │   (Mosquitto no PC) │  │
│                               │                     │  │
│  ┌──────────────┐    MQTT     │  temptf/sensor/dht22│  │
│  │ ESP32 + DHT11│──────────►  │  temptf/sensor/dht11│  │
│  │ (Arduino)    │             │  temptf/sensor/lm35 │  │
│  └──────────────┘             └─────────┬───────────┘  │
│                                         │              │
│  ┌──────────────┐    MQTT               │ subscribe    │
│  │ RPi + LM35  │──────────►            │              │
│  │ (Python)     │             ┌─────────▼───────────┐  │
│  └──────────────┘             │   voter.py (PC)     │  │
│                               │   Lógica de votação │  │
│                               │   Exibe temperatura │  │
│                               └─────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Protocolo MQTT — Tópicos

| Tópico                  | Publicado por     | Conteúdo                        |
|-------------------------|-------------------|---------------------------------|
| `temptf/sensor/dht22`   | ESP32 DHT22       | JSON com temperatura e status   |
| `temptf/sensor/dht11`   | ESP32 DHT11       | JSON com temperatura e status   |
| `temptf/sensor/lm35`    | Raspberry Pi LM35 | JSON com temperatura e status   |
| `temptf/status/dht22`   | ESP32 DHT22       | Heartbeat de boot               |

### Exemplo de payload:
```json
{
  "sensor":      "DHT22_ESP32",
  "temperature": 22.45,
  "status":      "OK",
  "cv":          2.31,
  "ts":          123456789
}
```
**Valores de `status`:**
- `OK` → média dentro do CV, valor é checkpoint novo
- `CHECKPOINT` → CV excedido, transmitindo último valor seguro
- `NO_CHECKPOINT` → CV excedido e ainda sem checkpoint (primeiros ciclos)

---

## Lógica do sensor (main.py)

```
A cada 500 ms → lê DHT22 → adiciona à janela deslizante [10 valores]
                                         │
A cada 5 s ──────────────────────────────┘
     │
     ├─ Calcula CV = (σ / |μ|) × 100
     │
     ├─ CV ≤ 10%?  ──SIM──► Checkpoint = média  ──► Publica (OK)
     │
     └─ CV > 10%?  ──SIM──► Tem checkpoint? ──SIM──► Publica (CHECKPOINT)
                                             ──NÃO──► Publica média (NO_CHECKPOINT)
```

---

## Lógica do votador (voter.py)

```
Recebe temp dos 3 sensores → calcula x̄ dos ativos
         │
         ├─ Algum sensor diverge > 10% de x̄?
         │       ├─ SIM → MASCARAMENTO DE FALHA
         │       └─ NÃO → CONSENSO: exibe menor temperatura
         │
         ├─ Sensor com 3 divergências consecutivas → ISOLADO
         │       ├─ 2 sensores restantes concordam → DEGRADADO (menor temp)
         │       └─ 2 sensores restantes divergem  → INSTÁVEL (última temp segura)
         │
         └─ Sensor isolado concorda por 3 ciclos → RECUPERADO
                 └─ Todos concordam por 3 ciclos → CONSENSO TOTAL restaurado
```

---

## Conexão do DHT22 ao ESP32

```
DHT22          ESP32
  VCC  ──────  3.3V (ou 5V)
  DATA ──────  GPIO4  (definido em config.py → DHT_PIN = 4)
  GND  ──────  GND

  ⚠ Adicionar resistor pull-up de 10kΩ entre DATA e VCC!
```

---

## Dependências

### ESP32 (MicroPython)
- `dht` — built-in no MicroPython padrão
- `umqtt.simple` — built-in no MicroPython padrão
- `network` — built-in no MicroPython padrão

### PC (voter.py)
```bash
pip install paho-mqtt

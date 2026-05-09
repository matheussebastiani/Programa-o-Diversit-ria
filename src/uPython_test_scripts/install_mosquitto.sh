#!/bin/bash

echo "Instalando Mosquitto..."

sudo apt update && sudo apt upgrade -y
sudo apt install mosquitto mosquitto-clients -y

echo "Setando as configurações necessárias para o Mosquitto funcionar com o ESP32..."

sudo tee /etc/mosquitto/conf.d/local.conf > /dev/null <<EOF
listener 1883
allow_anonymous true
EOF

sudo systemctl restart mosquitto
sudo systemctl enable mosquitto

printf "\e[32mConfiguração concluída. Teste com: mosquitto_sub -h IP_HOST -t teste/topico\e[0m\n"

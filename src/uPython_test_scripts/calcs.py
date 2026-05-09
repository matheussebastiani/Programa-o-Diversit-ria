import time

def calcular_media(leituras):
    soma = sum(leituras)
    m = soma / len(leituras)
    return m

def calcular_desvio_padrao(leituras, media):
    soma_quadrados = 0.0
    for i in range(len(leituras)):
        soma_quadrados += (leituras[i] - media) ** 2
        print(f"{leituras[i]}: ({leituras[i]} - {media} ** 2)")
        
    s = (soma_quadrados / (len(leituras) - 1) ) ** 0.5
    
    return s

valores = [1.8, 2.5, 3.4, 4.2, 5.0, 5.0]

med = calcular_media(valores)

s = calcular_desvio_padrao(valores, med)

cv = (s/med) * 100

print(f"Media: {med:.2f}, DP: {s:.2f}, CV: {cv:.2f}%")

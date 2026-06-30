import time
import random
import requests
import os

from dotenv import load_dotenv

# ===================== DEFININDO AMBIENTE =====================
load_dotenv()

random.seed() # Sem semente fixa para gerar valores mais imprevisíveis a cada execução

# ===================== CONFIGURAÇÕES DE REDE =====================
GATEWAY_IP = os.getenv("GATEWAY_IP", "0.0.0.0")
PORTA = os.getenv("PORTA", "8000")

URL_POST_SENSOR = f"http://{GATEWAY_IP}:{PORTA}/api/sensor"

# ===================== EMULAÇÃO DO SENSOR (DISTÂNCIA) =====================
SENSOR_ID = "sensor_distancia_1"  # Identificador único caso houvessem múltiplos sensores

def gerar_distancia_simulada():
    """Gera uma distância simulada (sensor ultrassônico), inteira, entre 0 e 4 metros."""
    return random.randint(0, 4)


def enviar_distancia(distancia):
    """Imprime e envia a distância gerada para o PC Gateway."""
    print(f"[SENSOR] Nova distância calculada pelo modelo: {distancia} m") # Print obrigatório do valor calculado antes de enviar

    payload = {"sensor_id": SENSOR_ID, "valor": distancia}
    try:
        resposta = requests.post(URL_POST_SENSOR, json=payload, timeout=3)
        if resposta.status_code == 200:
            print(f"[SENSOR] -> Sucesso: Dados transmitidos ao Gateway ({distancia} m)")
        else:
            print(f"[SENSOR] -> Gateway respondeu com status {resposta.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"[ERRO SENSOR] Não foi possível conectar ao PC Gateway: {e}")

# ===================== LOOP PRINCIPAL =====================
def loop_emulador():
    ultima_leitura_sensor = 0
    intervalo_sensor = 5

    while True:
        tempo_agora = time.time()

        # Gerar, Printar e Enviar
        if tempo_agora - ultima_leitura_sensor >= intervalo_sensor:
            distancia = gerar_distancia_simulada()
            enviar_distancia(distancia)
            ultima_leitura_sensor = tempo_agora

        time.sleep(intervalo_sensor)


if __name__ == "__main__":
    print("=" * 55)
    print(" Iniciando Emulador de Hardware de Contingência ")
    print("=" * 55)
    loop_emulador()
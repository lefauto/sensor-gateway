import json
import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, request, jsonify
import pika
import redis

app = Flask(__name__)
load_dotenv()

# ===================== CREDENCIAIS =====================
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "5000"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_KEY = os.getenv("REDIS_KEY", "")

CLOUDAMQP_URL = os.getenv("CLOUDAMQP_URL", "")
QUEUE_SENSOR = os.getenv("QUEUE_SENSOR", "")

# ===================== CONEXÕES =====================
r = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    decode_responses=True,
    ssl=True,  # Redis Cloud normalmente exige TLS; remova se seu plano não usar
)


def conectar_lavinmq():
    """Cria uma conexão/canal novo com o LavinMQ a partir da URL de conexão (AMQP)."""
    parametros = pika.URLParameters(CLOUDAMQP_URL)
    conexao = pika.BlockingConnection(parametros)
    canal = conexao.channel()
    canal.queue_declare(queue=QUEUE_SENSOR, durable=True)
    return conexao, canal


def publicar_na_fila(payload: dict):
    """Publica a leitura do sensor na fila do LavinMQ."""
    conexao, canal = conectar_lavinmq()
    try:
        canal.basic_publish(
            exchange="",
            routing_key=QUEUE_SENSOR,
            body=json.dumps(payload),
            properties=pika.BasicProperties(
                delivery_mode=2,  # mensagem persistente
                content_type="application/json",
            ),
        )
        print(f"[GATEWAY->LAVINMQ] Mensagem publicada na fila '{QUEUE_SENSOR}': {payload}")
    finally:
        conexao.close()


def atualizar_redis(valor: float):
    """Atualiza o valor mais recente da distância no Redis Cloud."""
    r.set(REDIS_KEY, valor)
    r.set(f"{REDIS_KEY}:timestamp", datetime.utcnow().isoformat())
    print(f"[GATEWAY->REDIS] Chave '{REDIS_KEY}' atualizada com valor: {valor}")


# ===================== ROTAS HTTP =====================
@app.route("/api/sensor", methods=["POST"])
def receber_sensor():
    """
    Recebe a leitura do sensor via POST.
    Payload esperado: {"sensor_id": "...", "valor": 3}  (valor em metros, inteiro 0-4)
    """
    dados = request.get_json(force=True)
    sensor_id = dados.get("sensor_id")
    valor = dados.get("valor")

    if valor is None:
        return jsonify({"erro": "Campo 'valor' é obrigatório"}), 400

    print(f"[GATEWAY] Recebido do sensor '{sensor_id}': {valor} m")

    payload_fila = {
        "sensor_id": sensor_id,
        "valor": valor,
        "timestamp": datetime.utcnow().isoformat(),
    }

    try:
        # 1) Publica no LavinMQ (mensageria assíncrona compartilhada)
        publicar_na_fila(payload_fila)
    except Exception as e:
        print(f"[ERRO LAVINMQ] {e}")
        return jsonify({"erro": f"Falha ao publicar no LavinMQ: {e}"}), 500

    try:
        # 2) Atualiza o Redis Cloud (cache do último valor)
        atualizar_redis(valor)
    except Exception as e:
        print(f"[ERRO REDIS] {e}")
        return jsonify({"erro": f"Falha ao atualizar Redis: {e}"}), 500

    return jsonify({"status": "ok", "valor_recebido": valor}), 200


if __name__ == "__main__":
    print("=" * 55)
    print(" Iniciando PC Gateway (Nó de Borda)")
    print("=" * 55)
    app.run(host="10.2.179.36", port=5000)
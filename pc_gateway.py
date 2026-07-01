import asyncio
import json
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, request, jsonify
import pika
import redis.asyncio as redis_async

app = Flask(__name__)
load_dotenv()

# ===================== CREDENCIAIS =====================
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "5000"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_KEY = os.getenv("REDIS_KEY", "")

CLOUDAMQP_URL = os.getenv("CLOUDAMQP_URL", "")
QUEUE_SENSOR = os.getenv("QUEUE_SENSOR", "")

GATEWAY_IP = os.getenv("GATEWAY_IP", "0.0.0.0")
PORTA = int(os.getenv("PORTA", "8000"))

# ===================== CONEXÕES =====================
def criar_cliente_redis():
    """Cria um cliente Redis assíncrono ligado ao loop atual."""
    return redis_async.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=5,
    )


def conectar_lavinmq():
    """Cria uma conexão/canal novo com o LavinMQ."""
    parametros = pika.URLParameters(CLOUDAMQP_URL)
    conexao = pika.BlockingConnection(parametros)
    canal = conexao.channel()
    canal.queue_declare(queue=QUEUE_SENSOR, durable=True)
    return conexao, canal


def _publicar_na_fila_sync(payload: dict):
    """Publica a leitura do sensor na fila do LavinMQ usando conexão síncrona."""
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


async def publicar_na_fila(payload: dict):
    """Publica a leitura do sensor na fila do LavinMQ sem bloquear o loop de eventos."""
    await asyncio.to_thread(_publicar_na_fila_sync, payload)


async def atualizar_redis(valor: float):
    """Atualiza o valor mais recente da distância no Redis Cloud."""
    cliente_redis = criar_cliente_redis()
    try:
        await cliente_redis.set(REDIS_KEY, valor)
        await cliente_redis.set(f"{REDIS_KEY}:timestamp", datetime.now(timezone.utc).isoformat())
        print(f"[GATEWAY->REDIS] Chave '{REDIS_KEY}' atualizada com valor: {valor}")
    finally:
        await cliente_redis.aclose()


# ===================== ROTAS HTTP =====================
@app.route("/api/sensor", methods=["POST"])
async def receber_sensor():
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        # 1) Publica no LavinMQ (mensageria assíncrona compartilhada)
        await publicar_na_fila(payload_fila)
    except Exception as e:
        print(f"[ERRO LAVINMQ] {e}")
        return jsonify({"erro": f"Falha ao publicar no LavinMQ: {e}"}), 500

    try:
        # 2) Atualiza o Redis Cloud (cache do último valor)
        await atualizar_redis(valor)
    except Exception as e:
        print(f"[ERRO REDIS] {e}")
        return jsonify({"erro": f"Falha ao atualizar Redis: {e}"}), 500

    return jsonify({"status": "ok", "valor_recebido": valor}), 200


if __name__ == "__main__":
    print("=" * 55)
    print(" Iniciando PC Gateway (Nó de Borda)")
    print("=" * 55)
    app.run(host=GATEWAY_IP, port=PORTA)
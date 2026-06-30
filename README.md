# Sensor Gateway

Este projeto implementa um gateway de borda para receber leituras de distância de um sensor, publicar os dados em uma fila de mensagens e atualizar o último valor em Redis.

## Visão Geral

O fluxo principal é:

1. O arquivo [sensor.py](sensor.py) gera uma distância simulada a cada 5 segundos.
2. O arquivo [pc_gateway.py](pc_gateway.py) recebe a leitura via HTTP em `/api/sensor`.
3. O gateway publica a leitura em uma fila do CloudAMQP/LavinMQ.
4. O gateway grava o valor mais recente no Redis.

## Estrutura do Projeto

- [pc_gateway.py](pc_gateway.py) — servidor Flask responsável por receber os dados do sensor.
- [sensor.py](sensor.py) — emulador do sensor que envia leituras periódicas.
- [requirements.txt](requirements.txt) — dependências Python do projeto.
- [.env.example](.env.example) — exemplo de variáveis de ambiente.

## Requisitos

- Python 3.10+
- Dependências listadas em [requirements.txt](requirements.txt)
- Instância Redis acessível
- Instância CloudAMQP/LavinMQ com fila configurada

## Configuração

1. Crie um ambiente virtual:

```bash
python -m venv .venv
```

2. Ative o ambiente virtual:

- Windows:

```bash
source .venv/Scripts/activate
```

- macOS/Linux:

```bash
source .venv/bin/activate
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Copie o arquivo de exemplo e configure as variáveis:

```bash
copy .env.example .env
```

Edite o arquivo [.env](.env) com os valores corretos:

```env
REDIS_HOST=seu_host
REDIS_PORT=sua_porta
REDIS_PASSWORD=sua_senha
REDIS_KEY=sua_chave

CLOUDAMQP_URL=url_de_seu_amqp
QUEUE_SENSOR=sua_fila

GATEWAY_IP=seu_ip_especifico
PORTA=sua_porta
```

## Como Executar

### 1. Iniciar o Gateway

```bash
python pc_gateway.py
```

O gateway ficará escutando em `localhost` por padrão (o host e a porta estão definidos no código).

### 2. Iniciar o Emulador de Sensor

Em outro terminal, execute:

```bash
python sensor.py
```

O emulador envia uma leitura simulada a cada 5 segundos para o endpoint:

```http
POST /api/sensor
```

Payload esperado:

```json
{
  "sensor_id": "sensor_distancia_1",
  "valor": 3
}
```

## Observações

- O gateway publica a leitura em fila para consumo assíncrono.
- O valor recebido é armazenado no Redis como o último ponto medido.
- O sensor pode ser substituído por um hardware real no futuro, mantendo a mesma API.

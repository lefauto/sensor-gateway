# Loop de eventos assíncrono e IDs de conexão

## Loop assíncrono

O fluxo assíncrono do gateway é baseado em funções `async` do Python:

1. A rota [pc_gateway.py](pc_gateway.py) recebe a leitura em `receber_sensor()`.
2. O endpoint chama `await publicar_na_fila(payload_fila)` para enviar a mensagem para o LavinMQ.
3. Em seguida, chama `await atualizar_redis(valor)` para gravar o valor mais recente no Redis.
4. A função `publicar_na_fila()` usa `await asyncio.to_thread(...)` para executar a publicação bloqueante em uma thread separada, evitando travar o loop principal de eventos.
5. As operações do Redis usam `await` diretamente no cliente `redis.asyncio`, então o runtime consegue continuar processando outras tarefas enquanto espera a resposta.

Em resumo, o loop de eventos do `asyncio` coordena as tarefas e só bloqueia nas chamadas que realmente precisam esperar I/O externo.            

## IDs de conexão

O projeto não gera IDs de conexão manualmente com `uuid` ou hash.

- Para o Redis, a conexão é aberta por `redis_async.Redis(...)`, e o gerenciamento do identificador interno fica a cargo da biblioteca.
- Para o LavinMQ, a conexão é criada por `pika.BlockingConnection(...)`, também com identificação interna controlada pelo driver.
- Portanto, não existe lógica customizada de geração de IDs no código; os identificadores são tratados internamente pelas bibliotecas utilizadas.
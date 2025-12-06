import pika
from laboratory.utils import current_time
import simplejson as json


def publish_to_exchange():
    # Подключение к RabbitMQ
    credentials = pika.PlainCredentials('guest', 'guest')  # если требуется аутентификация
    parameters = pika.ConnectionParameters(
        host='localhost',
        port=5672,
        credentials=credentials,
        virtual_host='/'  # виртуальный хост
    )

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    # Параметры существующего обменника (убедитесь, что он уже создан)
    exchange_name = 'sendresult'
    exchange_type = 'direct'  # или 'topic', 'fanout', 'headers'

    # Публикация сообщения
    message = {
        'timestamp': current_time(),
        'data': 'Hello RabbitMQ!',
        'type': 'test_message'
    }

    # Если нужно опубликовать в конкретный routing_key
    routing_key = 'route_sendresult_q'

    channel.basic_publish(
        exchange=exchange_name,
        routing_key=routing_key,
        body='Hello World!',
        properties=pika.BasicProperties(
            delivery_mode=2,  # persistent сообщение
            content_type='application/json'
        )
    )

    print(f" [x] Sent message to exchange '{exchange_name}' with routing key '{routing_key}'")
    connection.close()


def start_send_msg(message):
    credentials = pika.PlainCredentials('guest', 'guest')  # если требуется аутентификация
    parameters = pika.ConnectionParameters(
        host='localhost',
        port=5672,
        credentials=credentials,
        virtual_host='/'  # виртуальный хост
    )
    exchange_name = 'sendresult'
    cur_time = current_time().strftime("%d.%m.%y %H:%M:%S")
    message = {
        'timestamp': cur_time,
        'data': f"{message} -{cur_time}",
        'type': 'test_message'
    }

    routing_key = 'route_sendresult_q'
    with pika.BlockingConnection(parameters) as conn:
        with conn.channel() as ch:
            ch.basic_publish(
                exchange=exchange_name,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # persistent сообщение
                    content_type='application/json'
                )
            )


def process_message(*args):
    for arg in args:
        print(arg, "\n\n")

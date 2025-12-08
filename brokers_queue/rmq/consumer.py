import pika


def process_message(ch, method, properties, body):
    print(f"сообщение {body.decode()}")
    print(f"delivery_tag {method.delivery_tag}")
    ch.basic_ack(delivery_tag=method.delivery_tag)


def start_get_msg():
    credentials = pika.PlainCredentials('guest', 'guest')  # если требуется аутентификация
    parameters = pika.ConnectionParameters(
        host='localhost',
        port=5672,
        credentials=credentials,
        virtual_host='/'  # виртуальный хост
    )
    with pika.BlockingConnection(parameters) as conn:
        with conn.channel() as ch:
            ch.basic_consume(
                queue="sendresult_q",
                on_message_callback=process_message
            )

            print("Ождиаю событие")
            ch.start_consuming()

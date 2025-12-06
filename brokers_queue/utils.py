


def start_get_msg():
    credentials = pika.PlainCredentials('guest', 'guest')  # если требуется аутентификация
    parameters = pika.ConnectionParameters(
        host='localhost',
        port=5672,
        credentials=credentials,
        virtual_host='/'  # виртуальный хост
    )
    exchange_name = 'sendresult'

    message = {
        'timestamp': current_time().strftime("%d.%m.%y %H:%M:%S"),
        'data': 'Hello RabbitMQ!',
        'type': 'test_message'
    }

    with pika.BlockingConnection(parameters) as conn:
        with conn.channel() as ch:
            ch.basic_consume(
                queue="sendresult_q",
                on_message_callback=process_message
            )

            print("Ождиаю событие")
            ch.start_consuming()

import pika
from laboratory.settings import RMQ_AUTH_PARAM
from laboratory.utils import current_time
import simplejson as json


def broker_publish_msg(message):
    credentials = pika.PlainCredentials(RMQ_AUTH_PARAM.get("login"), RMQ_AUTH_PARAM.get("password"))  # если требуется аутентификация
    parameters = pika.ConnectionParameters(host=RMQ_AUTH_PARAM.get("address"), port=RMQ_AUTH_PARAM.get("port"), credentials=credentials, virtual_host='/')

    exchange_name = RMQ_AUTH_PARAM.get("exchange_name")

    cur_time = current_time().strftime("%Y%m%d%H:%M:%S")
    message = {'timestamp': cur_time, 'data': f"{message}", 'type': 'direction'}

    routing_key = RMQ_AUTH_PARAM.get("routing_key")
    with pika.BlockingConnection(parameters) as conn:
        with conn.channel() as ch:
            ch.basic_publish(
                exchange=exchange_name,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    content_type='application/json',
                ),
                mandatory=True,
            )

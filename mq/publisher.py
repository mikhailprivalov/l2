from laboratory.settings import RMQ_URL, DEPRECATED_RMQ_ENABLED


def mq_send(m_type, m_obj, m_pk, queue='l2_models_events'):
    if not DEPRECATED_RMQ_ENABLED:
        return
    import pika

    try:
        connection = pika.BlockingConnection(pika.URLParameters(RMQ_URL))
        channel = connection.channel()
        channel.queue_declare(queue=queue)
        channel.basic_publish(exchange='', routing_key='l2_models_events', body="{}|{}|{}".format(m_type, m_obj, m_pk))
        connection.close()
    except:
        import logging

        logger = logging.getLogger("pika")
        from traceback import format_exc

        logger.error(format_exc())


def get_queue_messages_count(queue='l2_models_events'):
    if not DEPRECATED_RMQ_ENABLED:
        return 0
    import pika

    try:
        connection = pika.BlockingConnection(pika.URLParameters(RMQ_URL))
        channel = connection.channel()
        channel.queue_declare(queue=queue)
        q = channel.queue_declare(queue=queue, passive=True)
        qq = str(q.method.__dict__)
        connection.close()
        return qq
    except:
        import logging

        logger = logging.getLogger("pika")
        from traceback import format_exc

        logger.error(format_exc())
        return 0

import json

from fpesa.postgres import Message, with_session, create_all
from fpesa.rabbitmq import get_connection


@with_session
def message_post(session, message_data):
    message = Message(message_data)
    session.add(message)


@with_session
def message_get(session, pagination_id, offset, limit):
    pass


def message_post_worker():
    def on_message(channel, method_frame, header_frame, body):
        message_post(json.loads(body.decode())['data'])
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    create_all()
    connection = get_connection()
    channel = connection.channel()
    channel.basic_consume(on_message, '/messages/:POST')
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()

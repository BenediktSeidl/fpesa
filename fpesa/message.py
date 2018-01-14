"""
-----------------------
message bus to database
-----------------------
"""
import json

import pika

from fpesa.postgres import Message, with_session, create_all
from fpesa.rabbitmq import get_connection


@with_session
def message_post(session, message_data):
    """
    save message to database.

    :param sqlalchemy.orm.session.Session session: session object injected via
        :py:func:`fpesa.postgres.with_session` decorator.
    :param dict message_data: a json serializeable python dictionary

    """
    message = Message(message_data)
    session.add(message)


@with_session
def message_get(session, pagination_id, offset, limit):
    """
    Fetch messages from database, newest to oldest.

    :param sqlalchemy.orm.session.Session session: session object injected via
        :py:func:`fpesa.postgres.with_session` decorator.
    :param int pagination_id: As new messages are inserted constantly it's
        necessary to freeze the pagination in place, otherwise one could see
        message twice when switching to the next page. The pagination_id is
        provided with the first result of message_get
    :param int offset: how many message should be skipped
    :param int limit: how many messages should be returned (max: 100)
    :rtype: dict

    TODO: explain dict structure
    """
    if pagination_id is None:
        # TODO: problem with no entries
        pagination_id = session.query(Message)\
            .order_by(Message.id.desc())\
            .limit(1)\
            .one().id
    total = session.query(Message)\
        .filter(Message.id <= pagination_id)\
        .count()
    query = session.query(Message)\
        .filter(Message.id <= pagination_id)\
        .order_by(Message.id.desc())\
        .offset(offset)\
        .limit(limit)
    return {
        'paginationId': pagination_id,
        'offset': offset,
        'limit': limit,
        'total': total,
        'messages': [m.message for m in query]
    }


def message_post_worker():
    """
    worker that keeps calling :py:func:`message_post` for each message that
    arrives on the message bus.
    """
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

def message_get_worker():
    """
    """
    # TODO: c&p!

    def on_message(channel, method_frame, header_frame, body):

        request_arguments = json.loads(body.decode())['args']

        pagination_id = request_arguments.get('paginationId', None)
        offset = request_arguments['offset']
        limit = request_arguments['limit']

        response = message_get(pagination_id, offset, limit)

        channel.publish(
            'RPC', header_frame.reply_to, json.dumps(response),
            pika.BasicProperties(correlation_id=header_frame.correlation_id)
        )

        channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    create_all()
    connection = get_connection()
    channel = connection.channel()
    channel.basic_consume(on_message, '/messages/:GET')
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()

"""
-----------------------
message bus to database
-----------------------
"""
import json

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
    pass


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

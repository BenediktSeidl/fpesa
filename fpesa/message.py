"""
-----------------------
message bus to database
-----------------------
"""
import json
import traceback

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
def message_get(session, request_arguments):
    """
    Fetch messages from database, newest to oldest.

    :param sqlalchemy.orm.session.Session session: session object injected via
        :py:func:`fpesa.postgres.with_session` decorator.

    :param dict request_arguments: :py:func:dict with request parameters

    # TODO: fix this docs

        :param int pagination_id: As new messages are inserted constantly it's
            necessary to freeze the pagination in place, otherwise one could
            see message twice when switching to the next page. The
            pagination_id is provided with the first result of message_get
        :param int offset: how many message should be skipped
        :param int limit: how many messages should be returned (max: 100)

    :rtype: dict

    TODO: explain dict structure
    """

    pagination_id = request_arguments.get('paginationId', None)
    offset = int(request_arguments['offset'])
    limit = int(request_arguments['limit'])

    if session.query(Message).count() == 0:
        return {
            'paginationId': 0,
            'offset': offset,
            'limit': limit,
            'total': 0,
            'messages': [],
        }

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
        # when an error occures, the message will not be acked, but the worker
        # will exit. the worker will then be restarted by the supervisor and
        # the problem will persist. but as the queue is persistant no messages
        # get lost
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


def _message_get_worker_cb(
        channel, method_frame, header_frame, body, debug=False):
    # when an error occures the error should be sent to the client and the
    # message should be acked anyway.
    try:
        request_arguments = json.loads(body.decode())['args']

        response = message_get(request_arguments)
    except Exception as e:
        if not debug:
            description = "Internal server error"
        else:
            description = "".join(traceback.format_exc())
        response = {'error': {'code': 500, 'description': description}}

    channel.publish(
        'RPC', header_frame.reply_to, json.dumps(response),
        pika.BasicProperties(correlation_id=header_frame.correlation_id)
    )

    channel.basic_ack(delivery_tag=method_frame.delivery_tag)


def message_get_worker(options):
    """
    """
    create_all()
    connection = get_connection()
    channel = connection.channel()
    channel.basic_consume(
        _message_get_worker_cb, '/messages/:GET',
        arguments={'debug': options.debug}
    )
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()

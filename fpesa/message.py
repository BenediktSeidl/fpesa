"""
------------------
message bus worker
------------------
"""
import json
import traceback
from functools import partial
import logging

import pika

from fpesa.postgres import Message, with_session, create_all
from fpesa.rabbitmq import open_connection

logger = logging.getLogger(__name__)


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

    :param dict request_arguments: request parameters of the corresponding http
        request. All entries are of the type ``str``. The keys of this
        dictionary are:

        * ``pagination_id`` As new messages are inserted constantly it's
          necessary to freeze the pagination in place, otherwise one could
          see message twice when switching to the next page. The
          pagination_id is provided with the first result of message_get
        * ``offset`` how many message should be skipped
        * ``limit`` how many messages should be returned (max: 100)

    :rtype: dict
    :returns: messages with additional meta information. The entries of the
        returned dictionary are:

        * ``paginationId`` may be resent with the next request to make the
          pagination immune against newly inserted messages
        * ``offset`` as provided with the request
        * ``limit`` as provided with the request
        * ``total`` number of elements available with this ``paginationId``
        * ``messages`` ``list`` of messages as inserted.
    """

    pagination_id = request_arguments.get('paginationId', None)
    if pagination_id is not None:
        pagination_id = int(pagination_id)
    offset = int(request_arguments['offset'])
    limit = min(100, int(request_arguments['limit']))

    if session.query(Message).count() == 0:
        return {
            'paginationId': 0,
            'offset': offset,
            'limit': limit,
            'total': 0,
            'messages': [],
        }

    if pagination_id is None:
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


def messages_post_worker():
    """
    worker that keeps calling :py:func:`message_post` for each message that
    arrives on the message bus.
    """
    def on_message(channel, method_frame, header_frame, body):
        logger.info(
            "message with delivery_tag={}".format(method_frame.delivery_tag))
        # when an error occures, the message will not be acked, but the worker
        # will exit. the worker will then be restarted by the supervisor and
        # the problem will persist. but as the queue is persistant no messages
        # get lost
        message_post(json.loads(body.decode())['data'])
        channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    create_all()
    connection = open_connection()
    channel = connection.channel()
    channel.queue_declare('/messages/:POST', durable=True)
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
    logger.info(
        "message with delivery_tag={}".format(method_frame.delivery_tag))
    try:
        request_arguments = json.loads(body.decode())['args']

        response = message_get(request_arguments)
    except Exception:
        logger.exception("Exception while handling message get")
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


def messages_get_worker(options):
    """
    worker that keeps calling :py:func:`message_get` for each message that
    arrives on the message bus.
    """
    create_all()
    connection = open_connection()
    channel = connection.channel()
    channel.queue_declare('/messages/:GET')
    channel.basic_consume(
        partial(_message_get_worker_cb, debug=options.debug), '/messages/:GET',
    )
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()

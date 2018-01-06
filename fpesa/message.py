from fpesa.postgres import Message, with_session


@with_session
def message_post(session, message_data):
    message = Message(message_data)
    session.add(message)


@with_session
def message_get(session, pagination_id, offset, limit):
    pass

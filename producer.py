import logging

from botocore.exceptions import ClientError

import queue_wrapper

logger = logging.getLogger(__name__)


def send_message(message_body, queue_name, message_attributes=None):
    """
    Send a message to an Amazon SQS queue.

    :param message_body: The body of the message.
    :param message_attributes: Custom attributes of the message. These are key-value
                               pairs that can be whatever you want.
    :return: The response from SQS that contains the assigned message ID.
    """
    queue = queue_wrapper.get_queue(queue_name)

    if not message_attributes:
        message_attributes = {}

    try:
        logger.info(
            f'Sending message to queue: {queue_name} with message: {message_body}')
        response = queue.send_message(
            MessageBody=message_body,
            MessageAttributes=message_attributes
        )
        logger.info('Message sent successfully')
    except ClientError as error:
        logger.exception(f'Send message failed: {message_body}')
        raise error
    else:
        return response

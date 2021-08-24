import os
import boto3

import logging
import queue_wrapper

import boto3
from botocore.exceptions import ClientError


logger = logging.getLogger(__name__)

queue_name = os.getenv('QUEUE_NAME')

def send_message(message_body, message_attributes=None):
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
        logger.info(f'Sending message to queue: {queue_name} with message: {message_body}')
        response = queue.send_message(
            MessageBody= message_body,
            MessageAttributes=message_attributes
        )
        logger.info(f'Message sent successfully')
    except ClientError as error:
        logger.exception("Send message failed: %s", message_body)
        raise error
    else:
        return response
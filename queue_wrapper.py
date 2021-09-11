import os
import logging

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

sqs = boto3.resource(
    'sqs',
    endpoint_url=os.getenv('SQS_URL')
)


def get_queue(name):
    """
    Gets an SQS queue by name.

    :param name: The name that was used to create the queue.
    :return: A Queue object.
    """
    try:
        queue = sqs.get_queue_by_name(QueueName=name)
        logger.info("Got queue '%s' with URL=%s", name, queue.url)
    except ClientError as error:
        logger.exception("Couldn't get queue named %s.", name)
        raise error
    else:
        return queue

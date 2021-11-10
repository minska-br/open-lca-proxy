import logging
import os
import json
import boto3

from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

host = os.getenv('ELASTICSEARCH_URL')
region = os.getenv('AWS_DEFAULT_REGION')

service = 'es'
credentials = boto3.Session().get_credentials()

awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

logger = logging.getLogger(__name__)

def connect_elasticsearch():
    _elasticsearch_client = OpenSearch(
        hosts = [{'host': host, 'port': 443}],
        http_auth = awsauth,
        use_ssl = True,
        verify_certs = True,
        connection_class = RequestsHttpConnection
    )

    if _elasticsearch_client.ping():
        logger.info('Elasticsearch connected !')
    else:
        logger.info('Awww it could not connect Elasticsearch!')
    return _elasticsearch_client

def create_index(elasticsearch_client, index_name='processes'):
    created = False

    settings = {
        "mappings": {
            "properties": {
                "id": { "type": "text" },
                "name": { "type": "text" },
            }
        }
    }

    try:
        if not elasticsearch_client.indices.exists(index_name):
            elasticsearch_client.indices.create(index=index_name, body=settings)
            logger.info(f'Created index with name: {index_name}')
            created = True
    except Exception as ex:
        logger.info(str(ex))
    finally:
        return created

def delete_index(elasticsearch_client, index_name='processes'):
    elasticsearch_client.indices.delete(index=index_name)

def store_record(elasticsearch_object, record, index_name='processes'):
    try:
        elasticsearch_object.index(index=index_name, body=json.dumps(record))
    except Exception as ex:
        logger.info('Error in indexing data')
        logger.info(str(ex))

def search(elasticsearch_client, text, index_name='processes'):
    search = {"query": {"match": {"name": text}}}
    return elasticsearch_client.search(index=index_name, body=json.dumps(search))

import logging
import os
import json

from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)

def connect_elasticsearch():
    _elasticsearch_client = Elasticsearch(os.getenv('ELASTICSEARCH_URL'))
    if _elasticsearch_client.ping():
        logger.info('Elasticsearch connected 🎉')
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

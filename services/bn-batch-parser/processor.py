import json
from tkinter import E
import uuid
from http import HTTPStatus
from io import BytesIO
from typing import Final, Optional, Tuple
from zipfile import ZipFile

from google.cloud import storage
from google.cloud import tasks_v2
from lxml import etree

from config import config
from logger import logging


storage_client = storage.Client()

# XML Namespaces
# - brom: CRA BN Namespace
NS = {
    'brom': '{http://ccra.gc.ca/xml_schemas/brom}',
}

def bn_batch(message_data: dict) -> Tuple[str, int]:
    '''Process the bn batch file.'''

    file_name = message_data['name']
    bucket_name = message_data['bucket']
    logging.info(f'Processing file: {file_name}, bucket:{bucket_name}')

    blob = storage_client.bucket(bucket_name).blob(file_name)
    contents = blob.download_as_string()
    if not isinstance(contents, bytes):
        msg = (
            f'Invalid blob type for file: {file_name}'
        )
        logging.error(f'error: {msg}')
        return f'Bad Request: {msg}', HTTPStatus.BAD_REQUEST

    parseXML(BytesIO(contents))

    try:
        logging.info(f'archiving file: {file_name}')
        _archive_completed_batch(contents, file_name)
        try:
            _delete_blob(bucket_name, file_name)
        except Exception as err:
            logging.error('Unable to delete the file: {file_name} left in raw storage.', err)

    except Exception as err:
        # The error won't get raised, since we don't need to reprocess the file
        logging.error('Unable to archive the file: {file_name} left in raw storage.', err)

    return '', HTTPStatus.OK

def _archive_completed_batch(contents: str, blob_name: str):
    '''Uploads a file to the bucket.'''

    bucket_name = 'bn-raw-processed-dev'

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name + '.zip')

    archive = BytesIO()
    with ZipFile(archive, 'w') as zip_archive:
        with zip_archive.open(blob_name, 'w') as file1:
            file1.write(contents)
    gcs_file = blob.open(mode='wb')
    gcs_file.write(archive.getvalue())
    gcs_file.close()

def _delete_blob(bucket_name, blob_name):
    '''Deletes a blob from the bucket.'''
    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.delete()

def bn_batch_reader(xmlfile, parent_element: str = '*'):
    '''Read the xml file and emit top level elements.'''
    for event, element in etree.iterparse(xmlfile, 
            tag=parent_element):
        yield element

def parseXML(xmlfile):
    '''Execute event handlers as they are emitted from the XML stream.'''
    for element in bn_batch_reader(xmlfile, NS['brom']+'relationshipBroadcastA'):
        match element.tag:
            case '{http://ccra.gc.ca/xml_schemas/brom}relationshipBroadcastA':
                error_msg, error_code = move_message(element)
            case _:
                None
   
    return None

def move_message(element: etree._Element):
    '''Create the move message on the Task Queue.'''
    newBN = element.find(NS['brom']+'businessRegistrationNumber').text
    newProgram = element.find(NS['brom']+'businessProgramIdentifier').text
    newAccount = element.find(NS['brom']+'businessProgramAccountReferenceNumber').text

    oldBN = element.find(NS['brom']+'relatedBusinessRegistrationNumber').text
    oldProgram = element.find(NS['brom']+'relatedBusinessProgramAccountIdentifier').text
    oldAccount = element.find(NS['brom']+'relatedBusinessProgramReferenceNumber').text
    message = {
        'id': str(uuid.uuid4()),
        'oldBn': f'{oldBN}{oldProgram}{oldAccount}',
        'newBn': f'{newBN}{newProgram}{newAccount}'
    }
    logging.info(f'creating task for: {message}')
    try:
        create_http_task(message)
        return '', HTTPStatus.OK
    except Exception as err:
        msg = f"Unable post task: {message['id']}"
        logging.error(msg, err)
        return msg, HTTPStatus.INTERNAL_SERVER_ERROR


def create_http_task(payload: dict):
    '''Create a task for the queue with a dict payload.'''
    audience = config.TASK_AUDIENCE
    location = config.TASK_LOCATION
    project = config.TASK_PROJECT_ID
    queue = config.TASK_QUEUE_NAME
    service_account_email = config.TASK_SERVICE_ACCOUNT_EMAIL
    url = config.TASK_SERVICE_URL

    client = tasks_v2.CloudTasksClient()

    # Construct the fully qualified queue name.
    parent = client.queue_path(project, location, queue)

    # Construct the request body.
    task = {
        'http_request': {  # Specify the type of request.
            'http_method': tasks_v2.HttpMethod.POST,
            'url': url,  # The full url path that the task will be sent to.
            'oidc_token': {
                'service_account_email': service_account_email,
                'audience': audience,
            },
        }
    }

    if payload is not None:
        # The API expects a payload of type bytes.
        converted_payload = json.dumps(payload).encode()
        # converted_payload = payload.encode()

        # Add the payload to the request.
        task['http_request']['body'] = converted_payload

    # Use the client to build and send the task.
    response = client.create_task(request={'parent': parent, 'task': task})

    logging.info(f"Created task for id:{payload['id']}, name:{response.name}")
    return response

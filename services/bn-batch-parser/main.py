import base64
import json
import os
from http import HTTPStatus

from flask import Flask, request

import processor
from logger import logging

app = Flask(__name__)

@app.route('/', methods=['POST'])
def index():
    '''Handle BN messages delivered by pubsub http calls.'''
    
    if not (envelope := request.get_json()):
        msg = 'no Pub/Sub message received'
        logging.info(f'bad message: {msg}')
        return f'Bad Request: {msg}', HTTPStatus.BAD_REQUEST

    if not isinstance(envelope, dict) \
       or 'message' not in envelope \
       or not (pubsub_message := envelope.get('message')) \
       or not (isinstance(pubsub_message, dict) and 'data' in pubsub_message):
        msg = 'invalid Pub/Sub message format'
        logging.error(f'error: {msg}')
        return f'Bad Request: {msg}', HTTPStatus.BAD_REQUEST

    try:
        data = json.loads(base64.b64decode(pubsub_message['data']).decode())

    except Exception as e:
        msg = (
            'Invalid Pub/Sub message: '
            'data property is not valid base64 encoded JSON'
        )
        logging.error(f'error: {e}')
        return f'Bad Request: {msg}', HTTPStatus.BAD_REQUEST

    # Validate the message is a Cloud Storage event.
    if not data['name'] or not data['bucket']:
        msg = (
            'Invalid Cloud Storage notification: '
            'expected name and bucket properties'
        )
        logging.error(f'error: {msg}')
        return f'Bad Request: {msg}', HTTPStatus.BAD_REQUEST

    try:
        logging.info('Processing incoming storage message.')
        logging.debug('Dispatching processor for: {data}')

        error_msg, error_code = processor.bn_batch(data)
        return error_msg, error_code

    except Exception as e:
        logging.error(f'error: {e}')
        return '', HTTPStatus.INTERNAL_SERVER_ERROR


if __name__ == '__main__':
    PORT = int(os.getenv('PORT')) if os.getenv('PORT') else 8080

    # This is used when running locally. Gunicorn is used to run the
    # application on Cloud Run. See entrypoint in Dockerfile.
    app.run(host='127.0.0.1', port=PORT, debug=False)

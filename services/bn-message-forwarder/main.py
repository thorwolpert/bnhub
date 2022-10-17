# Copyright 2019 Google, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START cloudrun_pubsub_server_setup]
# [START run_pubsub_server_setup]
import base64
import imp
import json
import logging
import os
from http import HTTPStatus

import requests
from flask import Flask, request

from config import Config
from iam import JWTService

config = Config()
logging.basicConfig(format='%(name)s - %(levelname)s:%(message)s',
                    level=config.LOG_LEVEL)

app = Flask(__name__)
app.config.from_object(config)


@app.route("/", methods=["POST"])
def index():
    '''Receive task messages.'''
    logging.debug('Receiving a task message.')

    payload = request.get_data()
    if not (json_data := json.loads(payload.decode('utf-8'))):
        msg = f'Bad data format: {payload}'
        logging.error(msg)
        return msg, HTTPStatus.BAD_REQUEST

    logging.debug(f'Received task: {json_data}')

    jwt_service = JWTService(config.OIDC_TOKEN_URL, config.OIDC_SA_CLIENT_ID, config.OIDC_SA_CLIENT_SECRET)
    token = jwt_service.get_token()

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    url = f'{config.BUSINESS_API_URL}/api/v2/internal/bnmove'
    logging.debug(f'Calling API, url: {url}, data: {json_data}')
    rv = requests.post(url=url,
                       headers=headers,
                       data=json.dumps(json_data))

    # check
    if rv.status_code in (HTTPStatus.CREATED, HTTPStatus.OK):
        logging.debug(f'Successfully forwarded: {json_data}')
        return '', rv.status_code

    logging.error(f'Failed to forward message: {json_data}')
    return None, HTTPStatus.BAD_REQUEST


if __name__ == "__main__":
    PORT = int(os.getenv("PORT")) if os.getenv("PORT") else 8080

    # This is used when running locally. Gunicorn is used to run the
    # application on Cloud Run. See entrypoint in Dockerfile.
    app.run(host="127.0.0.1", port=PORT, debug=True)

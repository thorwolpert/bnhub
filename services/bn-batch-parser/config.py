# Copyright © 2021 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The application common configuration."""
import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


class BaseConfig:
    """Base configuration."""


class Config(BaseConfig):
    """Production configuration."""
    #
    # Application Config
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')

    # Storage
    BUCKET_NAME_INCOMING = os.getenv('BUCKET_NAME_INCOMING')
    BUCKET_NAME_ARCHIVE = os.getenv('BUCKET_NAME_ARCHIVE')

    # TASK Configuration
    TASK_PROJECT_ID = os.getenv('TASK_PROJECT_ID')
    TASK_QUEUE_NAME = os.getenv('TASK_QUEUE_NAME')
    TASK_LOCATION = os.getenv('TASK_LOCATION')
    TASK_SERVICE_URL = os.getenv('TASK_SERVICE_URL')
    TASK_AUDIENCE = os.getenv('TASK_AUDIENCE')
    TASK_SERVICE_ACCOUNT_EMAIL = os.getenv('TASK_SERVICE_ACCOUNT_EMAIL')

config = Config()
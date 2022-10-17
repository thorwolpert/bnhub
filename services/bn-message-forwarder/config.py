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

    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')

    # OIDC and Authorization Config
    OIDC_TOKEN_URL = os.getenv('OIDC_TOKEN_URL')
    OIDC_SA_CLIENT_ID = os.getenv('OIDC_SA_CLIENT_ID')
    OIDC_SA_CLIENT_SECRET = os.getenv('OIDC_SA_CLIENT_SECRET')

    # BCRegistry API Config
    BUSINESS_API_URL = os.getenv('BUSINESS_API_URL')

    # BCRegistry Service Config
    REPORT_SVC_URL = os.getenv('REPORT_SVC_URL')

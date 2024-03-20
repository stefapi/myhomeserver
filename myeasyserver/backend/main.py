#  Copyright (c) 2024  stefapi
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import uvicorn
import json
import os

from myeasyserver.app import app_class
from ..version import __software__

__SOFTWARE__ = __software__.upper()
class backend_application(app_class):

    default_config = {
    }

    params_link = {
    }
    def __init__(self):
        pass

    @staticmethod
    def subparser():
        return ( "serve", "Start MyeasyServer backend")

    @staticmethod
    def params(parser):
        pass

    def test_name(self, name):
        return name == 'myeasysrv'
    def run(self, config):

        # Save here all program parameters for each FastAPI instances
        os.environ["ENVIRON_FOR_CHILD_PROCESS"] = json.dumps(vars(config.args))

        # Start uvicorn
        if config['internal.debug'] == True:
            serverconf = {
                'log_level': 'debug',
                'workers': 1
            }
            if config['application.socket'] is not None:
                serverconf['uds']= config['application.socket']
            else:
                serverconf['host'] = "0.0.0.0"
                serverconf['port'] = 8080
            if config['internal.development'] == True:
                serverconf['reload'] = True
                serverconf['reload_dirs'] = ["myeasyserver"]
        else: # production configuration here
            serverconf = {
                'log_level': 'debug' if config['application.verbose'] else 'error',
                'workers': 1
            }
            if config['application.socket'] is not None:
                serverconf['uds']= config['application.socket']
            else:
                serverconf['host'] = config['application.ip_address']
                serverconf['port'] = config['application.port']
        uvicorn.run(
            "myeasyserver.backend.webserver:app",
            **serverconf
        )


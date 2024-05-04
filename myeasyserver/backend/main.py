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
import signal
import sys
from time import sleep

import uvicorn
import json
import os
from myeasyserver.core.daemon import start_daemon

from myeasyserver.app import app_class
from ..version import __software__

__SOFTWARE__ = __software__.upper()
class backend_application(app_class):

    default_config = {
        'application': {
            'pid_file': '/var/run/' + __software__ + '.pid',
        }
    }

    params_link = {
        'application.pid_file': ['pid_file', __SOFTWARE__ + '_PID_FILE', 'PID_FILE'],
    }
    def __init__(self):
        pass

    @staticmethod
    def subparser():
        return ( "serve", "Start %s backend"%__software__ )

    @staticmethod
    def params(parser):
        parser.add_argument('--pid_file', default=None, help='pid file')
        parser.add_argument('--daemon', help='start as daemon', action='store_true')

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
                serverconf['reload_dirs'] = [__software__]
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
        serverconf['app'] = "%s.backend.webserver:app"%__software__
        # Start uvicorn as a daemon
        try:
            if config.args.daemon:
                return start_daemon(uvicorn.run, serverconf, config['application.pid_file'])
            else:
                try:
                    uvicorn.run(**serverconf)
                except KeyboardInterrupt:
                    print("caught keyboard interrupt, exiting")
        except Exception as e:
            print("Error:", str(e))
            sys.exit(1)

        return 0


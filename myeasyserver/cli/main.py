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

default_config = {
}

params_link = {
}

class cli_application(app_class):
    def __init__(self):
        pass

    @staticmethod
    def subparser():
        return ( "cli", "Command line tool to manage myEasyServer" )

    @staticmethod
    def params(parser):
        pass


    def test_name(self, name):
        return name == 'myeasycli'
    def run(self, config):
        pass



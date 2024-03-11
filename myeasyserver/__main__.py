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

import sys
from os.path import basename
from .core.arg_params import arg_parser
from .core.config import create_config
#from .cli import cli_application
#from .backend import backend_application

import uvicorn

def main():
    print("hello")
    Params = sys.argv
    #    if environ.get('DISPLAY') is None:
    #        Params.append('--nox')

    #app_envs = [cli_application(), backend_application()]
    app_envs = []

    app_name = basename(Params[0])

    # detect app kind based on program name prefix
    selected_app = None
    for app in app_envs:
        if app_name.startswith(app.binary_prefix()):
            selected_app = app

    # based on app detected apply the right parser
    if selected_app is None:
        parser = arg_parser(app_envs)
    else:
        parser = arg_parser([selected_app], False)

    # parse everything
    args = parser.parse_args(Params)

    config = create_config(args)
    # separate config file generation from appsettings generation

    if args.version == True:
        parser.print_version()
        exit(0)

    if args.write_conf is not None:
        config.writeto(args.write_conf, False)
        print("Configuration file is written to %s. Exiting." % args.write_conf)
    #uvicorn.run("webserver:app", host="0.0.0.0", port=8080, reload=True, log_level="debug", workers=1)
    uvicorn.run("myeasyserver.webserver:app", host="0.0.0.0", port=8080, uds="./webserver.sock", log_level="debug", workers=1)

if __name__ == "__main__":
    main()


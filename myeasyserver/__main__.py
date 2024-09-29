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

import argparse
import sys
from os.path import basename

from myeasyserver.app import app_store
from .core.arg_params import arg_parser
from .core.config import create_config
from .version import __software__, __description__, __version__
from .cli.main import cli_application
from .backend.main import backend_application

import uvicorn

__SOFTWARE__ = __software__.upper()

# default configuration attribute stored in configuration file (useful for command line program)
# internal items are not stored but are used internally
# you may use <> to define repetitive items
default_config = {
    'application': {
        'verbose': False,
        'ip_address': '127.0.0.1',
        'port': 8080,
        'socket': None,
        'default_group': 'default',
        'default_user': 'admin',
        'default_password': 'changeme',
        'default_hasher': 'argon2', # bcrypt, argon2
        'security_max_login_attempts': 5,
        'token_time': 48, # in hours
        'token_long_time': 24*365*5,  # in hours (5 years)
    },
    'internal': {
        'simulate': False,
        'development': False,
        'debug': False,
        'noauth': False,
        'demo': False,
    },
}

# each long name option has to be defined into basic_options
params_link = { # configuration attribute  [ long name option, Environment attribute , .env attribute]
    'internal.debug': ['debug_do_not_use', __SOFTWARE__ + '_DEBUG', 'DEBUG'],
    'internal.simulate': ['simulate_do_not_use', __SOFTWARE__ + '_SIMULATE', 'SIMULATE'],
    'internal.development': ['development_do_not_use', __SOFTWARE__ + '_DEVEL', 'DEVELOPMENT'],
    'internal.noauth': ['noauth_do_not_use', __SOFTWARE__ + '_DEVEL', 'NOAUTH'],
    'internal.demo': ['demo', __SOFTWARE__ + '_DEMO', 'DEMO'],
    'application.verbose': ['verbose', __SOFTWARE__ + '_VERBOSE', 'VERBOSE'],
    'application.ip_address': ['ip_address[0]', __SOFTWARE__ + '_IP_ADDRESS', 'IP_ADDRESS'],
    'application.port': ['port[0]', __SOFTWARE__ + '_PORT', 'PORT'],
    'application.socket': ['socket[0]', __SOFTWARE__ + '_SOCKET', 'SOCKET'],
}

def basic_options(parser):
    parser.add_argument('-v', '--version', help='Print version and exit', action='store_true')
    parser.add_argument('-C', '--conf', help='Name of configuration file to read', nargs=1)
    parser.add_argument('-w', '--write', help='write local config to file ./myeasyserver.toml', action='store_true')
    parser.add_argument('-W', '--write-conf', help='Name of configuration file to write', nargs=1)
    parser.add_argument('-V', '--verbose', help='Name of configuration file', action='store_true')

    parser.add_argument('-A', '--ip-address', help='IP address to bind for the server', nargs=1)
    parser.add_argument('-p', '--port', help='port to bind for the server', nargs=1)
    parser.add_argument('-S', '--socket', help='socket file to bind for the server', nargs=1)

    parser.add_argument('--demo', help='Enable Demo Mode', action='store_true')

    parser.add_argument('--debug_do_not_use', help=argparse.SUPPRESS, action='store_true')
    parser.add_argument('--development_do_not_use', help=argparse.SUPPRESS, action='store_true')
    parser.add_argument('--simulate_do_not_use', help=argparse.SUPPRESS, action='store_true')
    parser.add_argument('--noauth_do_not_use', help=argparse.SUPPRESS, action='store_true')


def main():
    Params = sys.argv
    #    if environ.get('DISPLAY') is None:
    #        Params.append('--nox')

    apps_store = app_store([cli_application(), backend_application()])

    app_name = basename(Params[0])

    # detect app kind based on program name prefix
    selected_app = apps_store.selected_app(app_name)
    params_link_app = apps_store.update_params_link(params_link)
    default_config_app = apps_store.update_default_config(default_config)

    # based on app detected apply the right parser
    if selected_app is None:
        app_list = apps_store
        generic =True
    else:
        app_list = [selected_app]
        generic =False


    parser = arg_parser(__software__, __version__, __description__, basic_options, {'title': 'Operation mode', 'description': 'Select operation mode', 'help': 'get help with --help', 'dest': 'mode'}, app_list.apps, generic)
    # parse everything
    args = parser.parse_args(Params)

    config = create_config(args.conf, args, params_link_app, default_config_app, args.debug_do_not_use)
    # separate config file generation from appsettings generation

    if args.version == True:
        parser.print_version()
        exit(0)

    if args.mode == "serve":
        run_app = backend_application()
    else:
        run_app = cli_application()

    if args.write == True:
        config.writeto("./myeasyserver.toml", False)
        print("Configuration file is written to ./myeasyserver.toml. Exiting.")
        exit(0)
    if args.write_conf is not None:
        config.writeto(args.write_conf[0], False)
        print("Configuration file is written to %s. Exiting." % args.write_conf[0])
        exit(0)

    return run_app.run(config)

if __name__ == "__main__":
    ret = main()
    exit(ret)


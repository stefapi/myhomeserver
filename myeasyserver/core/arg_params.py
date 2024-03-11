#
# Copyright 2019 Stephane Apiou
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse

from ..version import __software__, __description__, __version__

__SOFTWARE__ = __software__.upper()
# each long name option has to be defined into arg_parse class
params_link = { # configuration attribute  [ long name option, Environment attribute , .env attribute]
    'application.development': ['development', __SOFTWARE__ + '_DEVEL', 'DEVELOPMENT'],
    'application.demo': [None, __SOFTWARE__ + '_DEMO', 'DEMO'],
    'application.verbose': ['verbose', __SOFTWARE__ + '_VERBOSE', 'VERBOSE'],
    'application.default_locale': [None, __SOFTWARE__ + '_DEFAULT_LOCALE', 'LOCALE'],
    'application.default_timezone': [None, __SOFTWARE__ + '_DEFAULT_TIMEZONE', 'TIMEZONE'],
}

default_config = {
    'application': {
        'development': True,
        'demo': True,
        'verbose': False,
        'default_locale': 'C',
        'default_timezone': 'UTC',

        'use_metrics': True,
        'align_partitions': True,
        'align_on_cylinders': False,
        'sectors_alignment': 2048,
    },
    'colors': {
        'ext4': '#8faad2'
    },
    'internal': {
        'show_test_command': False,
        'master_password': ''
    },
    'servers': {
        '<>': {
            'name': 'standard',
            'address': '',
            'port': '',
            'login': '',
            'password': '',
            'sudo': True,
            'sudo_pwd': ''
        }
    }
}
class arg_parser():
    def __init__(self, xvpm_instances = None, generic= True):
        self.parser = argparse.ArgumentParser(description="Manage Volumes, Partitions, Disks and Filesystems")
        self.parser.add_argument('-v', '--version', help='Print version and exit', action='store_true')
        self.parser.add_argument('-C', '--conf', help='Name of configuration file to read', nargs='?')
        self.parser.add_argument('-w', '--write', help='write local config at end of program', action='store_true')
        self.parser.add_argument('-W', '--write-conf', help='Name of configuration file to write', nargs='?')
        self.parser.add_argument('-V', '--verbose', help='Name of configuration file', action='store_true')
        self.parser.add_argument('-D', '--development', help='Used to run in development mode.', action='store_true')

        self.parser.add_argument('--remote', help='Connect to remote server with login and optional password.', metavar='<[confname=]login[:password]@server[:port][&sudopassword]>')
        self.parser.add_argument('--sudo', help='On remote server perform an sudo after login', nargs='?', metavar='<password>')

        if generic == True:
            if xvpm_instances is not None:
                subparsers = self.parser.add_subparsers( title = "UI", description ="define type of UI", help ="get help with --help", dest ="ui")
                for instance in xvpm_instances:
                    name = instance.subparser()
                    sub = subparsers.add_parser(name[0], help = name[1])
                    instance.params(sub)
        else:
            xvpm_instances[0].params(self.parser)

        self.parser.add_argument('device', help='Device on which operation is performed', nargs='?')

    def parse_args(self,args):
        res = self.parser.parse_args(args[1:])
        return res

    def parse_known_args(self,args):
        res = self.parser.parse_known_args(args[1:])
        return res

    def print_help(self):
        self.parser.print_help()

    def print_version(self):
        print(self.program + " version : "+ __version__)



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

class arg_parser():
    def __init__(self, program, version, description, basic_options, instances_desc = None,xvpm_instances = None, generic= True):
        self.version = version
        self.program = program
        self.parser = argparse.ArgumentParser(description=description)
        basic_options(self.parser)

        desc = {'title': 'mode', 'description': 'Select mode', 'help': 'get help with --help', 'dest': 'mode'}
        if instances_desc is not None:
            for key, value in instances_desc.items():
                desc[key] = value
        if generic == True:
            if xvpm_instances is not None and len(xvpm_instances) > 0:
                subparsers = self.parser.add_subparsers( title = desc['title'], description =desc['description'], help = desc['help'], dest = desc['dest'])
                for instance in xvpm_instances:
                    name = instance.subparser()
                    sub = subparsers.add_parser(name[0], help = name[1])
                    instance.params(sub)
        else:
            if xvpm_instances is not None and len(xvpm_instances) > 0:
                xvpm_instances[0].params(self.parser)


    def parse_args(self,args):
        res = self.parser.parse_args(args[1:])
        return res

    def parse_known_args(self,args):
        res = self.parser.parse_known_args(args[1:])
        return res

    def print_help(self):
        self.parser.print_help()

    def print_version(self):
        print(self.program + " version : "+ self.version)



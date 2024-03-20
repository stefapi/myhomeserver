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
#

import os
import sys

from .settings import EnumSettings, AppSettings


def has_system():
    import getpass
    user = getpass.getuser()
    if sys.platform == 'win32':
        try:
            # only windows users with admin privileges can read the C:\windows\temp
            temp = os.listdir(os.sep.join([os.environ.get('SystemRoot','C:\\windows'),'temp']))
        except:
            return (user,False)
        else:
            return (user,True)
    else:
        if os.geteuid() < 1000:
            return (user,True)
        else:
            return (user,False)


def create_config(conf_file, args, params_link, default_config, devel = False):
    if devel == True:
        env = EnumSettings.Debug
    elif  os.path.exists("/.dockerenv"):
        env = EnumSettings.Docker
    else:
        sysrights = has_system()
        if sysrights[1]:
            env = EnumSettings.System
        else:
            env = EnumSettings.User
    return AppSettings(env, conf_file, args, default_config, params_link)

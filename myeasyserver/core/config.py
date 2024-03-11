#  Copyright (c) 2022  stefapi
#  BSD Simplified License
#
#   Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
#   following conditions are met:
#   1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
#   disclaimer.
#   2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#   following disclaimer in the documentation and/or other materials provided with the distribution.
#   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
#   INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#   DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#   SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
#   WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
#   USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#

import os
import sys

from .arg_params import params_link, default_config
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


def create_config(args):
    if args.development == True:
        env = EnumSettings.Debug
    elif  os.path.exists("/.dockerenv"):
        env = EnumSettings.Docker
    else:
        sysrights = has_system()
        if sysrights[1]:
            env = EnumSettings.System
        else:
            env = EnumSettings.User
    return AppSettings(env, args, default_config, params_link)

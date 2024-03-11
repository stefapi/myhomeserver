#  Copyright (c) 2022  stefapi
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
import tempfile
import json
from pathlib import Path
from enum import Enum
from myeasyserver.helper.appdirs import AppDirs
from myeasyserver.helper.config_file import config_file

from myeasyserver.version import __software__, __author__
import dotenv

settings = None

class EnumSettings(Enum):
    Debug = 0
    Docker = 1
    System = 2
    User = 3

class AppDirectories:
    def __init__(self, env: EnumSettings):
        self.__appdirs = AppDirs(__software__, __author__)
        self.LIB_DIR = os.path.join(self.__appdirs.site_lib_dir)
        self.WEB_DIR = os.path.join(self.LIB_DIR, "client", "dist")
        self.SYSCONF_DIR = os.path.join(self.__appdirs.site_config_dir)

        if env == EnumSettings.Docker:
            self.DATA_DIR = os.path.expanduser("/app/data")
            self.LOG_DIR = os.path.join(self.DATA_DIR,"log")
            self.CONF_DIR = os.path.join(self.DATA_DIR,"conf")
        elif env == EnumSettings.Debug:
            self.DATA_DIR = os.path.join(self.__appdirs.site_lib_dir.parent,"dev","data")
            self.LOG_DIR = os.path.join(self.DATA_DIR,"log")
            self.CONF_DIR = os.path.join(self.DATA_DIR,"conf")
        elif env == EnumSettings.System:
            self.DATA_DIR = os.path.join(self.__appdirs.site_cache_dir)
            self.LOG_DIR = os.path.join(self.__appdirs.site_log_dir)
            self.CONF_DIR = os.path.join(self.__appdirs.site_config_dir)
        else:
            self.DATA_DIR = os.path.join(self.__appdirs.user_cache_dir)
            self.LOG_DIR = os.path.join(self.__appdirs.user_log_dir)
            self.CONF_DIR = os.path.join(self.__appdirs.user_config_dir)

        self.BACKUP_DIR = os.path.join(self.DATA_DIR,"backups")
        self.DEBUG_DIR = os.path.join(self.DATA_DIR,"debug")
        self.MIGRATION_DIR = os.path.join(self.DATA_DIR,"migration")
        self.TEMPLATE_DIR = os.path.join(self.DATA_DIR,"templates")
        self.USER_DIR = os.path.join(self.DATA_DIR,"users")
        if env in [EnumSettings.System, EnumSettings.User]:
            self.TEMP_DIR = os.path.join(tempfile.gettempdir(), __software__)
        else:
            self.TEMP_DIR = os.path.join(self.DATA_DIR,".temp")

        self.__ensure_directories(env == EnumSettings.System)

    def json(self, **kwargs):
        var = vars(self)
        del var["_AppDirectories__appdirs"]
        return json.dumps(var, **kwargs)

    def __ensure_directories(self, system=False):
        required_system_dirs = [
            self.BACKUP_DIR,
            self.DATA_DIR,
            self.DEBUG_DIR,
            self.LOG_DIR,
            self.MIGRATION_DIR,
            self.TEMPLATE_DIR,
            self.TEMP_DIR,
            self.USER_DIR,
        ]

        required_std_dirs = [
            self.BACKUP_DIR,
            self.CONF_DIR,
            self.DATA_DIR,
            self.DEBUG_DIR,
            self.LOG_DIR,
            self.MIGRATION_DIR,
            self.TEMPLATE_DIR,
            self.TEMP_DIR,
            self.USER_DIR,
        ]
        required_dirs = required_system_dirs if system else required_std_dirs
        for dir in required_dirs:
            Path(dir).mkdir(parents=True, exist_ok=True)

class AppSettings():
    def __init__(self, type : EnumSettings, args, default_config, params_link):
        self.default_config = default_config
        self.config = default_config.copy()
        self.params_link = params_link
        self.path = AppDirectories(type)
        self.args = args

        if type != EnumSettings.System and type != EnumSettings.User:
            dotenv.load_dotenv(Path(self.path.LIB_DIR).parent.joinpath(".env"))

        if self.args.conf is not None:
            self.etc_conf = config_file(default_config, self.args.conf)
            self.local_conf = None
        else:
            self.etc_conf = config_file(default_config, os.path.join(self.path.SYSCONF_DIR, "config.toml"))
            self.local_conf = config_file(default_config, os.path.join(self.path.CONF_DIR, "config.toml"))
        self.env_list = os.environ.copy()

        self.config_calc()
        self.config.confDir = self.local_conf.confDir
        self.config.confFile = self.local_conf.confFile

    def __getitem__(self, key):
        return self.config.get(*key.split('.'))

    def __setitem__(self, key, value):
        return self.config.set_modify(value, *key.split('.'))

    def __delitem__(self, key, value):
        return self.config.delete(*key.split('.'))

    def __contains__(self, key):
        return self.config.has(*key.split('.'))

    def config_calc(self):

        # set default parameters
        params = config_file(self.default_config, 'None')

        def get_environ(options):
            path = None
            for items in list(options):
                path = items if path == None else path+'.'+items
            if path in self.params_link:
                environ = self.params_link[path][1]
                if environ is not None:
                    environ = environ.upper()
                    if environ in self.env_list:
                        return self.env_list[environ]
            return None

        # apply environment variables
        params.override(get_environ, True)

        def get_dotenv(options):
            path = None
            for items in options:
                path = items if path == None else path+'.'+items
            if path in self.params_link:
                environ = self.params_link[path][2]
                if environ is not None:
                    environ = environ.upper()
                    if environ in self.env_list:
                        return self.env_list[environ]
            return None

        # apply .env parameters
        params.override(get_dotenv, True)

        # override with etc configuration file if any
        params.override(self.etc_conf.get_config, True)

        # override with local configuration file if any
        if self.local_conf is not None:
            params.override(self.local_conf.get_config, True)

        def get_option(options):
            path = None
            for items in options:
                path = items if path == None else path+'.'+items
            if path in self.params_link:
                option = self.params_link[path][0]
                if option is not None and  hasattr(self.args, option):
                    return getattr(self.args, option)
            return None

        # apply command line options
        params.override(get_option, True)
        self.config = params

    def writeto(self, filename, with_internal=False):
        """
        The writeto function writes the configuration to a file.
        It does not write the internal data, only what is visible to the user.

        :param self: Reference the object itself
        :param filename: Specify the file to write to
        :param with_internal: Determine if the internal data should be written to file
        :return: `none`
        """
        if not with_internal:
            data = self.config.filter_internal()
        else:
            data = self.config
        data.writeto(filename)

    def write(self, with_internal = False):
        """
        The write function writes the configuration to a file.
        It does not write the internal data, only what is visible to the user.

        :param self: Reference the object itself
        :param with_internal: Determine if the internal data should be written to file
        :return: `none`
        """
        if not with_internal:
            data = self.config.filter_internal()
        else:
            data = self.config
        data.write()


    def set(self):
        global settings

        settings = self
        pass



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
import json
import os
from copy import copy
from pathlib import Path

import toml
from .type_conv import to_type

class config_file():

    def __init__(self, default_config, file_name = "none"):
        """ On init, read the saved configuration file if exists which is stored in $HOME directory as .(app_name)
        if the file does not exists, the default configuration defined in this class is used.
        special cases:
        * if a parameter is defined in internal section, this parameter is never exported or defined if not explicitly
        defined by the user or the application. Most of the time this is used for internal purpose, debug or non disclosed
        functionalities
        * if a parameter is defined as <>, it's considered as a template parameter. It's convenient if for example you have to configure
        several items with the same structure. for example: account definitions, remote servers definitions ...
        Conformity of each element (section, setting, subsetting and type) is compared with the default configuration. If not compatible, the value is rejected silently
        TODO: No version management of the configuration file implemented so far.


        :param app_name:  the name of the application. this is used to define the name of parameter file
        :type app_name: str
        :param app_author:  the author of the application. This is used to define the path of the software.
        :type app_author: str
        :param default_config:  a recursive dictionary containing the configuration
        :type default_config: dictionary
        :param scope: the scope of configuration file: 'data', 'etc', 'local', 'path'
        :type scope: str
        :param file_name:  the name of the configuration file. default as 'conf.ini'
        :type file_name: str
        """

        self.default_config = default_config
        self.config = None
        if file_name != "none":
            self.confDir = Path(file_name).parent
            self.confFile = file_name
        else:
            self.confDir = None
            self.confFile = None

        if self.confFile is not None and os.path.isfile(self.confFile):
            readconfig = toml.load(self.confFile)
            self.new = False
        else:
            readconfig = {}
            self.new = True
        # normalize configuration
        # or create a new config structure based on default_config structure

        def get_elem(elem_list):
            if readconfig is None:
                return None
            cur_conf= None
            cur_subconf = readconfig
            for elem in elem_list:
                cur_conf = cur_subconf
                cur_subconf = cur_conf.get(elem)
                if cur_subconf is None:
                    # elem is not present in the configuration
                    return None
            if cur_conf is None:
                return None
            return cur_subconf

        self.override(get_elem)


    @staticmethod
    def level_treat(old_config, ref_config, item_getter, options, with_internal):
        new_config = {}
        genericEnv = False
        if "<>" in ref_config and len(ref_config) == 1:
            ref_section = set([] if old_config is None else old_config.keys())
            item_dict = item_getter(options)
            ref_section = list(ref_section | set([] if item_dict is None else item_dict.keys()))
            genericEnv = True
        else:
            ref_section = ref_config.keys()
        for section in ref_section:
            if old_config is not None and section in old_config:
                config_section = old_config[section]
            else:
                config_section = None

            if genericEnv:
                settings = ref_config["<>"]
            else:
                settings = ref_config[section]

            if not isinstance(settings, dict):
                if with_internal or section != 'internal':
                    val = item_getter(options + [section])
                    if val is None:
                        if config_section is not None:
                            new_config[section] = to_type(settings, config_section)
                    else:
                        new_config[section] =  to_type(settings, val)
            else:
                if with_internal or section != 'internal':
                    results = config_file.level_treat(config_section, settings, item_getter, options + [section], with_internal)
                    if len(results) != 0:
                        new_config[section] = results
        return new_config

    def override(self, item_getter=None, with_internal=False):
        """
        The override function is used to override the current config with values from the injected_config.
        The override function takes a getter function as an argument, which is used to retrieve the value of a setting in injected_config.
        If no override function is given,it is assumed that item_getter is from config_file

        :param self: Access variables that belong to the class
        :param item_getter=None: Retrieve the value of a setting in injected_config
        :param with_internal=False: Ignore the internal section
        :return: A dictionary with the new configuration
        """

        #replace with the new configuration calculated
        self.config = config_file.level_treat(self.config, self.default_config, item_getter, [], with_internal)

    @staticmethod
    def __get_elem_generic(ref, config, options):
        """
        The __get_elem_generic function is a recursive function that takes three arguments:
        ref, config, and options. The ref argument is the reference to the configuration data.
        The config argument is a dictionary of dictionaries containing all of the sections in
        the configuration file with their respective keys and values. The options argument is
        a list of dictionary keys.

        :param ref: Store the configuration template
        :param config: Store the configuration data
        :param options: Specify the section and subsection of the config file that is being searched
        :return: A value from the configuration file
        """
        cur_ref = ref
        cur_config = config
        treated = []
        for elem in options:
            treated.append(elem)
            if len(cur_ref) == 1 and "<>" in cur_ref:
                ref_section = "<>"
            else:
                ref_section =elem
            if ref_section not in cur_ref:
                raise config_exception(treated)
            if elem not in cur_config:
                return None
            cur_ref = cur_ref[ref_section]
            cur_config = cur_config[elem]
        return cur_config

    def get_default(self, *args):
        """
        The get_default function returns the default value for a setting of a section.
        If the setting is a dictionary, it returns the dictionary. You may indicated
        a subsetting in order to obtain the value from the dictionary stored in
        the setting:

        :param self: Access the class attributes
        :param *args: Pass a variable number of arguments to a function
        :return: The default value for a setting of a section
        """
        return copy(config_file.__get_elem_generic(self.default_config, self.default_config, args))

    def get_config(self, *args):
        """
        The get_config function is used to get the value of a setting or subsetting.
        If no value is stored, the default value is returned.
        You may indicated a subsetting in order to obtain the value from the dictionary stored in the setting

        :param self: Reference the current instance of the class
        :param *args: Pass a variable number of arguments to a function
        :return: The value of the setting or subsetting
        """
        if len(args) == 1 and isinstance(args[0], list):
            args = tuple(args[0])
        return config_file.__get_elem_generic(self.default_config, self.config, args)

    def get(self, *args):
        """
        The get function returns the value of a config option.

        :param self: Access variables that belongs to the class
        :param *args: Pass a variable number of arguments to a function
        :return: The value of the key that is passed as an argument
        """
        ret = self.get_config(*args)
        if ret is None:
            return self.get_default(*args)
        return ret

    def set_modify(self, value, *args):
        """
        The set_modify function is used to set a value in the configuration file.
        The value to be set (value). This can be any type of data, but it must match the type of data that is expected for this key. For example, if a key expects

        :param self: Reference the class instance
        :param value: Set the value of the key in the configuration file
        :param *args: Pass a variable number of arguments to a function
        :return: The value written
        """

        cur_ref = self.default_config
        cur_config = self.config
        old_config = None
        treated = []
        for elem in args:
            treated.append(elem)
            if len(cur_ref) == 1 and "<>" in cur_ref:
                ref_section = "<>"
            else:
                ref_section =elem
            if ref_section not in cur_ref:
                raise config_exception(treated)
            if elem not in cur_config:
                cur_config[elem] = {}
            cur_ref = cur_ref[ref_section]
            old_config = cur_config
            cur_config = cur_config[elem]
        if old_config is not None:
            old_config[elem] = value
        return value

    def set_default(self, *args):
        """
        The set_default function is used to set the default value for a setting from a section. This is particularly useful for a setting based on a template in order to define the default values

        :param self: Access the attributes and methods of the class
        :param *args: Pass a variable number of arguments to select configuration element
        :return: The default value for a setting from a section
        """
        self.set_modify(self.get_default(*args), *args)

    def has(self, *args):
        """
        The has function checks if a setting is defined in the configuration.
        It can be used to check if a section exists or not, and it can also be used
        to check for specific settings within a section.

        :param self: Reference a class instance inside the class
        :param *args: Pass a non-keyworded, variable-length argument list
        :return: True if the setting is defined, false otherwise
        """

        cur_ref = self.default_config
        cur_config = self.config
        treated = []
        for elem in args:
            treated.append(elem)
            if len(cur_ref) == 1 and "<>" in cur_ref:
                ref_section = "<>"
            else:
                ref_section =elem
            if ref_section not in cur_ref:
                raise config_exception(treated)
            if elem not in cur_config:
                return False
            cur_ref = cur_ref[ref_section]
            cur_config = cur_config[elem]
        return True

    def delete(self, *args):
        """
        The delete function is used to delete a specific setting of a section. This is useful when a setting is defined based on
        a template setting. The function raises an exception if the section and/or settings are not defined.

        :param self: Access variables that are defined in the class
        :param *args: Pass a variable number of arguments to a function
        :return: True if the setting is deleted
        :doc-author: Trelent
        """
        """
        The delete function is used to delete a specific setting of a section. This is useful when a setting is defined based on
        a template setting. The function raises an exception if the section and/or settings are not defined.

        :param self: Access variables that are defined in the class
        :param section: Specify the section of the config file to be used
        :param setting: Delete a setting in the config file
        :return: Nothing
        """

        cur_ref = self.default_config
        cur_config = self.config
        treated = []
        old_config = None
        for elem in args:
            treated.append(elem)
            if len(cur_ref) == 1 and "<>" in cur_ref:
                ref_section = "<>"
            else:
                ref_section =elem
            if ref_section not in cur_ref:
                raise config_exception(treated)
            if elem not in cur_config:
                return False
            cur_ref = cur_ref[ref_section]
            old_config = cur_config
            cur_config = cur_config[elem]
        if old_config is not None:
            del old_config[elem]
            return True
        return False

    def filter_internal(self):
        """
        The filter_internal function is used to filter out the internal key from the configuration file.
        The value is a dictionary of all keys and values in the configuration file. The function will return a new dictionary with no internal key.

        :param self: Reference the class instance
        :param value: Set a value in the configuration file
        :return: A dictionary of all the keys in the configuration file that do not have a value of internal
        """

        def filter_internal_recur(value):
            new_config = {}
            for section, value in value.items():
                if not isinstance(value, dict):
                    if section != 'internal':
                        new_config[section] = value
                else:
                    if section != 'internal':
                        results =  filter_internal_recur(value)
                        if len(results) != 0:
                            new_config[section] = results
            return new_config

        newconf= config_file(self.default_config)
        newconf.confDir = self.confDir
        newconf.confFile = self.confFile
        newconf.config = filter_internal_recur(self.config)
        return newconf

    def write(self):
        """
        The write function writes the configuration file to disk's configuration directory.
        It does not write any other files, such as images or templates.

        :return: None
        """
        if self.confDir is None:
            return
        if self.confDir != '' and not os.path.exists(self.confDir):
            os.makedirs(self.confDir)
        return self.writeto(self.confFile)

    def writeto(self, filename):
        """
        The writeto function writes the configuration stored in the class as a toml file.

        :param filename: Specify the name of the file to which you want to write
        :return: Nothing
        """
        serialized = toml.dumps(self.config)
        with open(filename, 'w') as confFileid:
            confFileid.write(serialized)

    def enumerate(self, *args):
        """ iterate on each setting of a section if the section is defined. Iterate on each section if section is None

        :param section: section to enumerate. If None, enumerate all sections (setting value is ignored)
        :param setting: setting to enumerate. If None, enumerate all settings of a defined section
        :return: return a iterator that enumerate each item
        """
        cur_ref = self.default_config
        treated= []
        for elem in args:
            treated.append(elem)
            if len(cur_ref) == 1 and "<>" in cur_ref:
                ref_section = "<>"
            else:
                ref_section =elem
            if ref_section not in cur_ref:
                raise config_exception(treated)
            cur_ref = cur_ref[ref_section]

        for read_item in cur_ref.keys():
            yield read_item

    def json(self, **kwargs):
        return json.dumps(self.config, **kwargs)


class config_exception(Exception):
    """base config exception"""

    def __init__(self,sections = None, message="Exception in configuration"):
        self.sections = sections
        if sections is not None:
            if isinstance(sections, list):
                text = sections[0]
                for section in sections[1:]:
                    text += "->"+section
            else:
                text = sections
            message = text + " is not defined in configuration"
        self.message =  message
        super().__init__(message)


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
from myeasyserver.helper.config_file import config_file


class app_class:

    params_link = {}

    default_config = {}

    def __init__(self):
        pass

    @staticmethod
    def subparser():
        pass

    @staticmethod
    def test_name(name):
        return False

    @staticmethod
    def params(parser):
        pass
    def update_params_link(self,params_link):
        updt_link = self.params_link.copy()
        updt_link.update(params_link)
        return updt_link

    @staticmethod
    def __concat_dictionaries(dict1, dict2):
        """
        Concatenate two dictionaries containing dictionaries recursively.

        Args:
        dict1 (dict): The first dictionary.
        dict2 (dict): The second dictionary.

        Returns:
        dict: The concatenated dictionary.
        """
        result = dict1.copy()  # Copy the first dictionary to avoid modifying it

        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # If both values are dictionaries, recursively concatenate them
                result[key] =app_class.__concat_dictionaries(result[key], value)
            else:
                # Otherwise, simply update the value
                result[key] = value

        return result

    def update_default_config(self,default_config):
        updt_config = self.__concat_dictionaries(default_config, self.default_config)
        return updt_config



class app_store:
    def __init__(self, app_list = []):
        self.apps = app_list

    def add_app(self, app):
        self.apps.append(app)

    def selected_app(self, app_name):
        # detect app kind based on program name prefix
        selected_app = None
        for app in self.apps:
            if app.test_name(app_name):
                selected_app = app
        return selected_app

    def update_params_link(self,params_link):
        for app in self.apps:
            updt_link = app.update_params_link(params_link)
            params_link = updt_link
        return params_link

    def update_default_config(self,default_config):
        for app in self.apps:
            updt_config = app.update_default_config(default_config)
            default_config = updt_config
        return default_config



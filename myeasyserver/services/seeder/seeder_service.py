#  Copyright (c) 2024.  stef.
#
#      ______                 _____
#     / ____/___ ________  __/ ___/___  ______   _____  _____
#    / __/ / __ `/ ___/ / / /\__ \/ _ \/ ___/ | / / _ \/ ___/
#   / /___/ /_/ (__  ) /_/ /___/ /  __/ /   | |/ /  __/ /
#  /_____/\__,_/____/\__, //____/\___/_/    |___/\___/_/
#                   /____/
#
#  Apache License
#  ================
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
from ..base_service import BaseService
from ...database.repositories import AllRepositories
from ...schema.user import UserModel
from ...schema.user.user import GroupInDB


class SeederService(BaseService):
    def __init__(self, repos: AllRepositories, user: UserModel, group: GroupInDB):
        self.repos = repos
        self.user = user
        self.group = group
        super().__init__()

    def seed_Template(self, locale: str) -> None:
        #seeder = TemplateSeeder(self.repos, self.logger, self.group.id)
        #seeder.seed(locale)
        pass
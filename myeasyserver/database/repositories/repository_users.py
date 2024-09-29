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

import random
import shutil

from pydantic import UUID4
from pydantic.v1.schema import schema
from sqlalchemy import select

from .repository_generic import RepositoryGeneric
from ..models.users import User
from ...backend.config import config
from ...schema.user import UserModel


class RepositoryUsers(RepositoryGeneric[UserModel, User]):
    def update_password(self, id, password: str):
        entry = self._query_one(match_value=id)
        if config['internal.demo']:
            user_to_update = self.schema.model_validate(entry)
            if user_to_update.is_default_user:
                # do not update the default user in demo mode
                return user_to_update

        entry.update_password(password)
        self.session.commit()

        return self.schema.model_validate(entry)

    def create(self, user: User | UserModel | User | dict, schema = True) -> UserModel | User:  # type: ignore
        new_user = super().create(user, schema=schema)
        return new_user

    def update(self, match_value: str | int | UUID4, new_data: dict | UserModel | User, schema = True) -> User | UserModel:
        if config['internal.demo']:
            user_to_update = self.get_one(match_value, schema=schema)
            if user_to_update and user_to_update.is_default_user:
                # do not update the default user in demo mode
                return user_to_update

        return super().update(match_value, new_data, schema=schema)

    def delete(self, value: str | UUID4, match_key: str | None = None, schema = True) -> User | UserModel:
        if config['internal.demo']:
            user_to_delete = self.get_one(value, match_key, schema=schema)
            if user_to_delete and user_to_delete.is_default_user:
                # do not update the default user in demo mode
                return user_to_delete

        entry = super().delete(value, match_key, schema=schema)
        return entry

    def get_by_username(self, username: str, schema = True) -> User | UserModel | None:
        stmt = select(User).filter(User.username == username)
        dbuser = self.session.execute(stmt).scalars().one_or_none()
        if schema:
            return None if dbuser is None else self.schema.model_validate(dbuser)
        return dbuser

    def get_locked_users(self, schema = True) -> list[User | UserModel]:
        stmt = select(User).filter(User.locked_at != None)  # noqa E711
        results = self.session.execute(stmt).scalars().all()
        if schema:
            return [self.schema.model_validate(x) for x in results]
        return results



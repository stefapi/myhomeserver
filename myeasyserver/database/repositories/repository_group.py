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

from collections.abc import Iterable
from typing import cast
from uuid import UUID
from pydantic import UUID4
from slugify import slugify
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from .repository_generic import RepositoryGeneric
from ..models.group import Group
from ...schema.user.user import GroupInDB, GroupBase, UpdateGroup


class RepositoryGroup(RepositoryGeneric[GroupInDB, Group]):
    def create(self, data: GroupBase | dict) -> GroupInDB:
        if isinstance(data, GroupBase):
            data = data.model_dump()

        max_attempts = 10
        original_name = cast(str, data["name"])

        attempts = 0
        while True:
            try:
                return super().create(data)
            except IntegrityError:
                self.session.rollback()
                attempts += 1
                if attempts >= max_attempts:
                    raise

                data["name"] = f"{original_name} ({attempts})"

    def create_many(self, data: Iterable[GroupInDB | dict]) -> list[GroupInDB]:
        # since create uses special logic for resolving slugs, we don't want to use the standard create_many method
        return [self.create(new_group) for new_group in data]

    def update(self, match_value: str | int | UUID4, new_data: UpdateGroup | dict) -> GroupInDB:
        return super().update(match_value, new_data)

    def update_many(self, data: Iterable[UpdateGroup | dict]) -> list[GroupInDB]:
        # since update uses special logic for resolving slugs, we don't want to use the standard update_many method
        return [self.update(group["id"] if isinstance(group, dict) else group.id, group) for group in data]

    def get_by_name(self, name: str) -> GroupInDB | None:
        dbgroup = self.session.execute(select(self.model).filter_by(name=name)).scalars().one_or_none()
        if dbgroup is None:
            return None
        return self.schema.model_validate(dbgroup)

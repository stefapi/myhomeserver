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
from sqlalchemy import Column, Integer, String

from database.models.model_base import SqlAlchemyBase, BaseMixins


class Jobs_in_base(SqlAlchemyBase, BaseMixins):
    __tablename__ = 'jobs'
    id = Column(Integer, primary_key=True)
    job = Column(String)
    interval = Column(Integer)
    latest = Column(Integer)
    unit = Column(String)
    timezone = Column(String)
    startday = Column(String)
    cancel_after = Column(String)
    tags = Column(String)


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

from pydantic import UUID4, ConfigDict, BaseModel
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.interfaces import LoaderOption

from ...database.models.server.events import EventNotifierModel


# =============================================================================
# Group Events Notifier Options


class EventNotifierOptions(BaseModel):
    """
    These events are in-sync with the EventTypes found in the EventBusService.
    If you modify this, make sure to update the EventBusService as well.
    """

    test_message: bool = False
    webhook_task: bool = False

    recipe_created: bool = False
    recipe_updated: bool = False
    recipe_deleted: bool = False

    user_signup: bool = False

    data_migrations: bool = False
    data_export: bool = False
    data_import: bool = False

    mealplan_entry_created: bool = False

    shopping_list_created: bool = False
    shopping_list_updated: bool = False
    shopping_list_deleted: bool = False

    cookbook_created: bool = False
    cookbook_updated: bool = False
    cookbook_deleted: bool = False

    tag_created: bool = False
    tag_updated: bool = False
    tag_deleted: bool = False

    category_created: bool = False
    category_updated: bool = False
    category_deleted: bool = False


class EventNotifierOptionsSave(EventNotifierOptions):
    notifier_id: UUID4


class EventNotifierOptionsOut(EventNotifierOptions):
    id: UUID4
    model_config = ConfigDict(from_attributes=True)


# =======================================================================
# Notifiers


class GroupEventNotifierCreate(BaseModel):
    name: str
    apprise_url: str | None = None


class EventNotifierSave(GroupEventNotifierCreate):
    enabled: bool = True
    group_id: UUID4
    options: EventNotifierOptions = EventNotifierOptions()


class GroupEventNotifierUpdate(EventNotifierSave):
    id: UUID4
    apprise_url: str | None = None


class EventNotifierOut(BaseModel):
    id: UUID4
    name: str
    enabled: bool
    group_id: UUID4
    options: EventNotifierOptionsOut
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def loader_options(cls) -> list[LoaderOption]:
        return [joinedload(EventNotifierModel.options)]

class EventNotifierPrivate(EventNotifierOut):
    apprise_url: str
    model_config = ConfigDict(from_attributes=True)

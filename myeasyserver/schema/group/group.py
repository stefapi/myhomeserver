from pydantic import UUID4, BaseModel

from .group_preferences import UpdateGroupPreferences


class GroupAdminUpdate(BaseModel):
    id: UUID4
    name: str
    preferences: UpdateGroupPreferences | None = None

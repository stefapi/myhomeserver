from typing import TYPE_CHECKING, Optional

import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Mapped, mapped_column

from myeasyserver.helper.guid import GUID
from ..auto_init import auto_init
from ..model_base import SqlAlchemyBase, BaseMixins

if TYPE_CHECKING:
    from group import Group


class GroupPreferencesModel(SqlAlchemyBase, BaseMixins):
    __tablename__ = "group_preferences"
    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)

    group_id: Mapped[GUID | None] = mapped_column(GUID, sa.ForeignKey("groups.id"), nullable=False, index=True)
    group: Mapped[Optional["Group"]] = orm.relationship("Group", back_populates="preferences")

    private_group: Mapped[bool | None] = mapped_column(sa.Boolean, default=True)

    @auto_init()
    def __init__(self, **_) -> None:
        pass

from ..repositories import AllRepositories
from ...backend.config import config
from ...core.root_logger import get_logger
from ...schema.user import GroupBase
from ...services.group_service import GroupService

logger = get_logger()

def dev_groups() -> list[dict]:
    return [
        {
            "name": "alexgroup"
        },
        {
            "name": "othergroup"
        },
    ]


def default_group_init(db: AllRepositories):
    logger.info("Generating Default Group")
    GroupService.create_group(db, GroupBase(name=config['application.default_group']))

    if config['internal.development'] == True:
        for group in dev_groups():
            GroupService.create_group(db, GroupBase(name=group['name']))

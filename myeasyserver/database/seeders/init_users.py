from ..repositories import AllRepositories
from ...backend.config import config
from ...core.root_logger import get_logger
from ...core.security import hash_password

logger = get_logger()

def dev_users() -> list[dict]:
    return [
        {
            "full_name": "Robert",
            "username": "robert",
            "email": "robert@example.com",
            "password": hash_password(config['application.default_password']),
            "group": config['application.default_group'],
            "admin": False,
        },
        {
            "full_name": "Alex",
            "username": "alex",
            "email": "alex@example.com",
            "password": hash_password(config['application.default_password']),
            "group": "alexgroup",
            "admin": False,
        },
    ]


def default_user_init(db: AllRepositories):
    default_user = {
        "full_name": "Change Me",
        "username": config['application.default_user'],
        "email": "changeme@example.com",
        "password": hash_password(config['application.default_password']),
        "group": config['application.default_group'],
        "admin": True,
    }

    logger.info("Generating Default User")
    db.users.create(default_user)

    if config['internal.development'] == True:
        for user in dev_users():
            db.users.create(user)

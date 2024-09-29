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

import os
from collections.abc import Callable
from pathlib import Path
from time import sleep

from alembic import config, command, script
from sqlalchemy import engine, orm, text

from alembic.config import Config
from alembic.runtime import migration

from myeasyserver.database.models.model_base import SqlAlchemyBase
from .seeders.init_groups import default_group_init
from .seeders.init_users import default_user_init
from ..backend.config import config as backend_config
from .repositories.all_repositories import get_repositories
from .repositories import AllRepositories
from ..core.root_logger import get_logger
from .db_session import session_context, get_db_url
from .db_session import engine as db_engine
from ..backend.config import config as app_config
ALEMBIC_DIR = Path(__file__).parent.parent

logger = get_logger()


def init_db(db: AllRepositories) -> None:
    """
    Initialize the database with default data.
    """
    default_group_init(db)
    default_user_init(db)


# Adapted from https://alembic.sqlalchemy.org/en/latest/cookbook.html#test-current-database-revision-is-at-head-s
def db_is_at_head(alembic_cfg: config.Config) -> bool:
    url = get_db_url(backend_config["application.db_url"])

    connectable = engine.create_engine(url)
    directory = script.ScriptDirectory.from_config(alembic_cfg)
    with connectable.begin() as connection:
        context = migration.MigrationContext.configure(connection)
        return set(context.get_current_heads()) == set(directory.get_heads())


def safe_try(func: Callable):
    try:
        func()
    except Exception as e:
        logger.error(f"Error calling '{func.__name__}': {e}")


def connect(session: orm.Session) -> bool:
    try:
        session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return False


def main():

    if app_config['internal.debug'] and app_config['internal.development']:
        logger.info("Running in debug mode with development seeders.")
        logger.info("Database is created without Alembic")
        SqlAlchemyBase.metadata.create_all(db_engine)
    else:

        # TODO use environment variable or parameters instead
        max_retry = 10
        wait_seconds = 1


        # Wait for database to connect
        with session_context() as session:
            while True:
                if connect(session):
                    logger.info("Database connection established.")
                    break

                logger.error(f"Database connection failed. Retrying in {wait_seconds} seconds...")
                max_retry -= 1

                sleep(wait_seconds)

                if max_retry == 0:
                    raise ConnectionError("Database connection failed - exiting application.")

            alembic_cfg_path = os.getenv("ALEMBIC_CONFIG_FILE", default=str(ALEMBIC_DIR  / "alembic.ini"))

            if not os.path.isfile(alembic_cfg_path):
                raise Exception("Provided alembic config path doesn't exist")

            alembic_cfg = Config(alembic_cfg_path)
            if db_is_at_head(alembic_cfg):
                logger.debug("Migration not needed.")
            else:
                logger.info("Migration needed. Performing migration...")
                command.upgrade(alembic_cfg, "head")

        if session.get_bind().name == "postgresql":  # install pg_trgm extension for unanchored search patterns
            session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))

    with session_context() as session:
        db = get_repositories(session)

        if len(db.users.get_all()[0]):
            logger.debug("Database exists")
        else:
            logger.info("Database contains no users, initializing...")
            init_db(db)


if __name__ == "__main__":
    main()

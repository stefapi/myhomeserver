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
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from debug_toolbar.middleware import DebugToolbarMiddleware
from starlette.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

import services
from ..version import __version__, __software__, __description__


def api_middleware(app):
    from .config import config
    app.add_middleware( CORSMiddleware, allow_origins=config['cors.allow_origins'], allow_credentials=config['cors.allow_credentials'], allow_methods=config['cors.allow_methods'], allow_headers=config['cors.allow_headers'])
    app.add_middleware(DebugToolbarMiddleware, panels=['debug_toolbar.panels.sqlalchemy.SQLAlchemyPanel'])
    #app.add_middleware(PrometheusMiddleware, app_name=__software__, prefix=__software__)
    #app.add_route(settings['api.prometheus_url'], handle_metrics)

    app.add_middleware(GZipMiddleware, minimum_size=1000)
    #admin = Admin(
    #    engine,
    #    title = "MyEasyServer Database admin page",
    #)
    #admin.add_view(ModelView(SignUp, db.session))

    #from .db.sql_admin import register_admin
    #admin.mount_to(server)

    #register_admin(app)

def routers(app):
    from ..apisrv import router
    app.include_router(router)

def build_app():
    from .config import config

    @asynccontextmanager
    async def lifespan_handler(_: FastAPI) -> AsyncGenerator[None, None]:
        logger.info("start: database initialization")

        from ..database.init_db import main

        main()
        logger.info("end: database initialization")

        # from .services.events import create_general_event
        import myeasyserver.services.scheduler.execution_queue

        logger.info("-----SYSTEM STARTUP----- \n")
        logger.info("------APP SETTINGS------")
        logger.info(
            config.json(internal = config['internal.debug'])
        )
        logger.info(
            config.path.json(indent=4)
        )

        #create_general_event("Application Startup", f"API started on port {settings['application.port']}")
        #redis = aioredis.from_url(
        #    settings.REDIS_URL,
        #    decode_responses=True,
        #    encoding="utf8",
        #)
        yield

        logger.info("-----SYSTEM SHUTDOWN----- \n")


    server = FastAPI(
        debug = config['internal.debug'],
        title=__software__,
        description=__description__,
        version=__version__,
        docs_url = config['application.api_docs'] if config['application.api_docs'] else "",
        redoc_url = config['application.api_redoc'] if config['application.api_redoc'] else "",
        lifespan= lifespan_handler,
    )

    from ..core.root_logger import get_logger
    logger = get_logger()


    api_middleware(server)
    routers(server)
    return server

app = build_app()

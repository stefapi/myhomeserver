import json
import os
from argparse import Namespace

from .main import backend_application
from ..__main__ import params_link, default_config
from ..cli.main import cli_application
from ..core.config import create_config
from ..app import app_store

args = Namespace()
if "ENVIRON_FOR_CHILD_PROCESS" in os.environ:
    vars = json.loads(os.environ["ENVIRON_FOR_CHILD_PROCESS"])
    for k, v in vars.items():
        args.__setattr__(k, v)
else:
    args.conf = None
    args.debug_do_not_use = False

apps_store = app_store([cli_application(), backend_application()])
params_link_app = apps_store.update_params_link(params_link)
default_config_app = apps_store.update_default_config(default_config)
config = create_config(args.conf, args, params_link_app, default_config_app, args.debug_do_not_use)


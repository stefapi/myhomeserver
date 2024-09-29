import asyncio
import importlib

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker
import json

from .timed_tasks import run_pending
from .worker import worker_every
from ...core import root_logger

logger = root_logger.get_logger("jobs")

def serialize_function_call(method, *args, **kwargs):
    """
        Serialize a function call
    """

    method_name = f"{method.__module__}.{method.__qualname__}"

    call_details = {
        'method_name': method_name,
        'args': args,
        'kwargs': kwargs
    }

    return json.dumps(call_details)


def deserialize_and_execute(serialized_call):
    """
        Deserialize and execute a function call
    """

    call_details = json.loads(serialized_call)

    method_name = call_details['method_name']
    module_name, function_name = method_name.rsplit('.', 1)

    module = importlib.import_module(module_name)

    method_to_call = getattr(module, function_name)

    result = method_to_call(*call_details['args'], **call_details['kwargs'])

    return result

@worker_every(seconds=60, logger=logger)
async def run_jobs():
    """
    Run jobs in time order. This method is called every minute.
    Jobs a scheduled static tasks defined in the application
    """
    run_pending()

@worker_every(seconds=1, logger=logger)
async def run_tasks():
    """
    Run tasks sequentially from the execution pipeline. This method is called every second.
    Tasks are scheduled task that have to be executed immediately by the worker
    """
    pass

async def run_jobs_from_db():
    """
    Run jobs in time order. This method is called every second.
    Tasks are stored in DB and will survive the restart of the application or from the system
    they only are
    """
    engine = create_engine('sqlite:///tasks.db', echo=True)  # Connexion à la base de données SQLite
    #Base.metadata.create_all(engine)  # Créer la table des tâches si elle n'existe pas encore
    Session = sessionmaker(bind=engine)
    session = Session()

    semaphore = asyncio.Semaphore(3)  # Limite à trois tâches en parallèle
    tasks = []

    # Récupérer les tâches depuis la base de données
    #query = session.query(Jobs_in_base)
    #for task_row in query:
        #async with semaphore:
            #task_instance = task(task_row.x, task_row.y)
            #tasks.append(task_instance)
            #await asyncio.ensure_future(task_instance)

    # Fermer la session
    session.close()

    # Attendre que toutes les tâches soient terminées
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(run_tasks())

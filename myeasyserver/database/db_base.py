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

from typing import Union

from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import load_only
from sqlalchemy.orm.session import Session

from .models.model_base import SqlAlchemyBase
from ..core.root_logger import get_logger

logger = get_logger()


class BaseDocument:
    def __init__(self) -> None:
        self.primary_key: str
        self.store: str
        self.sql_model: SqlAlchemyBase
        self.schema: BaseModel

    def get_all(
        self, session: Session, limit: int = None, order_by: str = None, start=0, end=9999, override_schema=None
    ) -> list[dict]:
        """
        The get_all function is a convenience function that returns all the objects of a given type.
        It is equivalent to:
            session.query(MyModel).all()

        :param self: Used to Access attributes and methods of the class in python.
        :param session:Session: Used to Query the database.
        :param limit:int=None: Used to Limit the number of results returned.
        :param order_by:str=None: Used to Specify the order in which the results are returned.
        :param start=0: Used to Specify the offset of the query.
        :param end=9999: Used to Set the limit of records to be returned.
        :param override_schema=None: Used to Override the schema used to serialize the data.
        :return: A list of objects that are serialized using the schema.
        """
        eff_schema = override_schema or self.schema

        if order_by:
            order_attr = getattr(self.sql_model, str(order_by))

            return [
                eff_schema.from_orm(x)
                for x in session.query(self.sql_model).order_by(order_attr.desc()).offset(start).limit(limit).all()
            ]

        return [eff_schema.from_orm(x) for x in session.query(self.sql_model).offset(start).limit(limit).all()]

    def get_all_limit_columns(self, session: Session, fields: list[str], limit: int = None) -> list[SqlAlchemyBase]:
        """
        The get_all_limit_columns function is used to query the database for all values of a given model.
        The function takes in three parameters: session, fields, and limit. The session parameter is a SQLAlchemy
        Session Object that allows us to interact with the database directly through Python code. The fields parameter
        is a list of strings that contains the names of columns we want returned from our query (e.g., ['id', 'name']).
        Finally, the limit parameter is an integer value specifying how many rows we want returned from our query.

        :param self: Used to Access variables that belongs to the class.
        :param session:Session: Used to Access the database.
        :param fields:list[str]: Used to Specify which columns to return.
        :param limit:int=None: Used to Limit the number of responses from the database.
        :return: A list of the orm objects that are returned from the query.
        """
        return session.query(self.sql_model).options(load_only(*fields)).limit(limit).all()

    def get_all_primary_keys(self, session: Session) -> list[str]:
        """
        The get_all_primary_keys function queries the database of the selected model and returns a list
        of all primary_key values

        :param self: Used to Access variables that belongs to the class.
        :param session:Session: Used to Query the database.
        :return: A list of all primary_key values.
        """
        results = session.query(self.sql_model).options(load_only(str(self.primary_key)))
        results_as_dict = [x.dict() for x in results]
        return [x.get(self.primary_key) for x in results_as_dict]

    def _query_one(self, session: Session, match_value: str, match_key: str = None) -> SqlAlchemyBase:
        """
        The _query_one function is a helper function that will query the database for one item.
        It takes in three parameters: session, match_value, and match_key. The session is the sqlalchemy
        session object used to connect to the database. The match value is what we are looking for in our
        query (e.g., if you were searching by id it would be an int). And finally, the match key is what
        we are matching against (e.g., if you were searching by id it would be 'id'). It returns both a
        session and found model object.

        :param self: Used to Reference the class object within the function.
        :param session:Session: Used to Interact with the database.
        :param match_value:str: Used to Pass the value to use in the query.
        :param match_key:str=None: Used to Specify a key to use for the query.
        :return: A session object and an sqlalchemybase model.
        """

        if match_key is None:
            match_key = self.primary_key

        return session.query(self.sql_model).filter_by(**{match_key: match_value}).one()

    def get(
        self, session: Session, match_value: str, match_key: str = None, limit=1, any_case=False, override_schema=None
    ) -> Union[BaseModel, list[BaseModel]]:
        """
        The get function is used to retrieve a single entry from the database.
        It takes in a session object, and two strings: match_value and match_key.
        match_value is the value that will be matched against, while match_key is the key that will be used to perform this matching operation.
        If no key is provided then it defaults to using the primary key of its SQLAlchemy model for matching.

        :param self: Used to Reference the class object within the class itself.
        :param session:Session: Used to Access the database.
        :param match_value:str: Used to Match the value of a key/value pair in the database.
        :param match_key:str=None: Used to Match the key to use for matching.
        :param limit=1: Used to Ensure that the result is a single object and not a list of objects.
        :param any_case=False: Used to Match case sensitively.
        :param override_schema=None: Used to Override the schema used to serialize the data.
        :return: A list of results, but the schema only expects one result.
        """
        if match_key is None:
            match_key = self.primary_key

        if any_case:
            search_attr = getattr(self.sql_model, match_key)
            result = (
                session.query(self.sql_model).filter(func.lower(search_attr) == match_value.lower()).limit(limit).all()
            )
        else:
            result = session.query(self.sql_model).filter_by(**{match_key: match_value}).limit(limit).all()

        eff_schema = override_schema or self.schema

        if limit == 1:
            try:
                return eff_schema.from_orm(result[0])
            except IndexError:
                return None
        return [eff_schema.from_orm(x) for x in result]

    def create(self, session: Session, document: dict) -> BaseModel:
        """
        The create function creates a new database entry for the given SQL Alchemy Model.

        :param self: Used to Access variables that belongs to the class.
        :param session:Session: Used to Interact with the database.
        :param document:dict: Used to Pass in the python dictionary that is used to create a new database entry.
        :return: The new document as a dictionary.
        """
        document = document if isinstance(document, dict) else document.dict()

        new_document = self.sql_model(session=session, **document)
        session.add(new_document)
        session.commit()

        return self.schema.from_orm(new_document)

    def update(self, session: Session, match_value: str, new_data: dict) -> BaseModel:
        """
        The update function updates a database entry.

        :param self: Used to Access the class properties.
        :param session:Session: Used to Interact with the database.
        :param match_value:str: Used to Match the entry to be updated.
        :param new_data:dict: Used to Update the database entry with new data.
        :return: A dictionary representation of the database entry.
        """
        new_data = new_data if isinstance(new_data, dict) else new_data.dict()

        entry = self._query_one(session=session, match_value=match_value)
        entry.update(session=session, **new_data)

        session.commit()
        return self.schema.from_orm(entry)

    def patch(self, session: Session, match_value: str, new_data: dict) -> BaseModel:
        """
        The patch function is used to update an existing entry in the database.
        It takes a match_value (the value of the primary key) and new data as arguments.
        The function will return a BaseModel instance with the updated data.

        :param self: Used to Access the class instance inside the method.
        :param session:Session: Used to Interact with the database.
        :param match_value:str: Used to Find the entry in the database that needs to be updated.
        :param new_data:dict: Used to Update the entry that was found.
        :return: The updated entry.
        """
        new_data = new_data if isinstance(new_data, dict) else new_data.dict()

        entry = self._query_one(session=session, match_value=match_value)

        if not entry:
            return

        entry_as_dict = self.schema.from_orm(entry).dict()
        entry_as_dict.update(new_data)

        return self.update(session, match_value, entry_as_dict)

    def delete(self, session: Session, primary_key_value) -> dict:
        """
        The delete function deletes a row from the database.
        It takes in a session and primary_key_value as parameters.
        The function returns the deleted object as a dictionary.

        :param self: Used to Access variables that belongs to the class.
        :param session:Session: Used to Interact with the database.
        :param primary_key_value: Used to Find the row to delete.
        :return: A dictionary.
        """
        result = session.query(self.sql_model).filter_by(**{self.primary_key: primary_key_value}).one()
        results_as_model = self.schema.from_orm(result)

        session.delete(result)
        session.commit()

        return results_as_model

    def delete_all(self, session: Session) -> None:
        """
        The delete_all function deletes all rows from the table.

        :param self: Used to Access the class attributes.
        :param session:Session: Used to Access the database.
        :return: None.
        """
        session.query(self.sql_model).delete()
        session.commit()

    def count_all(self, session: Session, match_key=None, match_value=None) -> int:
        """
        The count_all function returns the number of rows in a table.

        :param self: Used to Access the attributes and methods of the class in python.
        :param session:Session: Used to Access the database.
        :param match_key=None: Used to Indicate that the function should return all of the instances of a class.
        :param match_value=None: Used to Specify that the function should return a count of all rows in the table.
        :return: The number of rows in the table.
        """
        if None in [match_key, match_value]:
            return session.query(self.sql_model).count()
        else:
            return session.query(self.sql_model).filter_by(**{match_key: match_value}).count()

    def _count_attribute(
        self, session: Session, attribute_name: str, attr_match: str = None, count=True, override_schema=None
    ) -> Union[int, BaseModel]:
        """
        The _count_attribute function is a helper function that is used to count the number of
           objects in the database. It takes an attribute name and an optional match value as arguments.
           If no match value is provided, it will return the total number of objects in the table.

        :param self: Used to Reference the class instance.
        :param session:Session: Used to Perform the query.
        :param attribute_name:str: Used to Specify the attribute that we want to count.
        :param attr_match:str=None: Used to Filter the query by a specific value.
        :param count=True: Used to Determine if we want to return the count of the number of objects that match a certain attribute or if we want to return an actual list of objects.
        :param override_schema=None: Used to Specify a different schema than the one specified in the class.
        :return: The number of rows in the table that match the attribute_name and attr_match.
        """
        eff_schema = override_schema or self.schema
        # attr_filter = getattr(self.sql_model, attribute_name)

        if count:
            return session.query(self.sql_model).filter(attribute_name == attr_match).count()  # noqa: 711
        else:
            return [
                eff_schema.from_orm(x)
                for x in session.query(self.sql_model).filter(attribute_name == attr_match).all()  # noqa: 711
            ]

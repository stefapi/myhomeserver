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

import re

from pydantic import BaseModel
from sqlalchemy import Select
from sqlalchemy.orm import Session
from text_unidecode import unidecode

from ....helper.types import SearchType
from ...models.model_base import SqlAlchemyBase


class SearchFilter:
    """
    0. fuzzy search (postgres only) and tokenized search are performed separately
    1. take search string and do a little pre-normalization
    2. look for internal quoted strings and keep them together as "literal" parts of the search
    3. remove special characters from each non-literal search string
    """

    punctuation = "!\#$%&()*+,-./:;<=>?@[\\]^_`{|}~"  # string.punctuation with ' & " removed
    quoted_regex = re.compile(r"""(["'])(?:(?=(\\?))\2.)*?\1""")
    remove_quotes_regex = re.compile(r"""['"](.*)['"]""")

    @classmethod
    def _normalize_search(cls, search: str, normalize_characters: bool) -> str:
        search = search.translate(str.maketrans(cls.punctuation, " " * len(cls.punctuation)))

        if normalize_characters:
            search = unidecode(search).lower().strip()
        else:
            search = search.strip()

        return search

    @classmethod
    def _build_search_list(cls, search: str) -> list[str]:
        if cls.quoted_regex.search(search):
            # all quoted strings
            quoted_search_list = [match.group() for match in cls.quoted_regex.finditer(search)]

            # remove outer quotes
            quoted_search_list = [cls.remove_quotes_regex.sub("\\1", x) for x in quoted_search_list]

            # punctuation->spaces for splitting, but only on unquoted strings
            search = cls.quoted_regex.sub("", search)  # remove all quoted strings, leaving just non-quoted
            search = search.translate(str.maketrans(cls.punctuation, " " * len(cls.punctuation)))

            # all unquoted strings
            unquoted_search_list = search.split()
            search_list = quoted_search_list + unquoted_search_list
        else:
            search_list = search.translate(str.maketrans(cls.punctuation, " " * len(cls.punctuation))).split()

        # remove padding whitespace inside quotes
        return [x.strip() for x in search_list]

    def __init__(self, session: Session, search: str, normalize_characters: bool = False) -> None:
        if session.get_bind().name != "postgresql" or self.quoted_regex.search(search.strip()):
            self.search_type = SearchType.tokenized
        else:
            self.search_type = SearchType.fuzzy

        self.session = session
        self.search = self._normalize_search(search, normalize_characters)
        self.search_list = self._build_search_list(self.search)

    def filter_query_by_search(self, query: Select, schema: type[BaseModel], model: type[SqlAlchemyBase]) -> Select:
        return schema.filter_search_query(model, query, self.session, self.search_type, self.search, self.search_list)

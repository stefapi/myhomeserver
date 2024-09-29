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

import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast


@dataclass(slots=True)
class JsonProvider:
    translations: dict

    def __init__(self, path: Path | dict):
        if isinstance(path, Path):
            self.translations = json.loads(path.read_text())
        else:
            self.translations = path

    def _parse_plurals(self, value: str, count: float):
        # based off of: https://kazupon.github.io/vue-i18n/guide/pluralization.html

        values = [v.strip() for v in value.split("|")]
        if len(values) == 1:
            return value
        elif len(values) == 2:
            return values[0] if count == 1 else values[1]
        elif len(values) == 3:
            if count == 0:
                return values[0]
            else:
                return values[1] if count == 1 else values[2]
        else:
            return values[0]

    def t(self, key: str, default=None, **kwargs) -> str:
        keys = key.split(".")

        translation_value: dict | str = self.translations
        last = len(keys) - 1

        for i, k in enumerate(keys):
            if k not in translation_value:
                break

            try:
                translation_value = translation_value[k]  # type: ignore
            except Exception:
                break

            if i == last:
                for key, value in kwargs.items():
                    translation_value = cast(str, translation_value)
                    if value is None:
                        value = ""
                    if key == "count":
                        translation_value = self._parse_plurals(translation_value, float(value))
                    translation_value = translation_value.replace("{" + key + "}", str(value))  # type: ignore
                return translation_value  # type: ignore

        return default or key

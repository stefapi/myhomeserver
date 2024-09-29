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

from dataclasses import dataclass, field
from pathlib import Path

from .json_provider import JsonProvider


@dataclass(slots=True)
class InUseProvider:
    provider: JsonProvider
    locks: int


@dataclass(slots=True)
class ProviderFactory:
    directory: Path
    fallback_locale: str = "en-US"
    filename_format = "{locale}.{format}"

    _store: dict[str, InUseProvider] = field(default_factory=dict)

    @property
    def fallback_file(self) -> Path:
        return self.directory / self.filename_format.format(locale=self.fallback_locale, format="json")

    def _load(self, locale: str) -> JsonProvider:
        filename = self.filename_format.format(locale=locale, format="json")
        path = self.directory / filename

        return JsonProvider(path) if path.exists() else JsonProvider(self.fallback_file)

    def release(self, locale) -> None:
        if locale in self._store:
            self._store[locale].locks -= 1
            if self._store[locale].locks == 0:
                del self._store[locale]

    def get(self, locale: str) -> JsonProvider:
        if locale in self._store:
            self._store[locale].locks += 1
        else:
            self._store[locale] = InUseProvider(provider=self._load(locale), locks=1)

        return self._store[locale].provider

# Copyright Software Improvement Group
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import hashlib
import os
from dataclasses import asdict
from datetime import datetime
from json import dump

import dateutil.parser


def parseDate(value):
    if value in (None, "", "None"):
        return None
    return dateutil.parser.isoparse(value)


def serialize(data, outputFile):
    os.makedirs(os.path.dirname(outputFile), exist_ok=True)
    with open(outputFile, "w", encoding="utf8") as f:
        dump(asdict(data), f, indent=4, default=serializeFieldToJSON)


def serializeFieldToJSON(field):
    if isinstance(field, datetime):
        return field.isoformat()
    raise TypeError(f"Cannot serialize field to JSON: {type(field)}")


def anonymize(text):
    return hashlib.sha256(text.encode("utf8")).hexdigest()

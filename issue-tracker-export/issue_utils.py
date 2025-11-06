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


def serialize(data, outputFile, anonymize):
    os.makedirs(os.path.dirname(outputFile), exist_ok=True)

    if anonymize:
        for issue in data.issues:
            issue.author = anonymizeAuthorName(issue.author) if issue.author else None
            issue.assignees = [anonymizeAuthorName(assignee) for assignee in issue.assignees]

    with open(outputFile, "w", encoding="utf8") as f:
        dump(asdict(data), f, indent=4, ensure_ascii=False, default=serializeFieldToJSON)


def serializeFieldToJSON(field):
    if isinstance(field, datetime):
        return field.isoformat()
    raise TypeError(f"Cannot serialize field to JSON: {type(field)}")


def anonymizeAuthorName(name):
    return hashlib.sha256(name.encode("utf8")).hexdigest()


def filterIssueData(issueData, excludeLabels):
    isExcluded = lambda labels: bool(set(labels) & set(excludeLabels))
    issueData.issues = [issue for issue in issueData.issues if not isExcluded(issue.labels)]
    issueData.epics = [epic for epic in issueData.epics if not isExcluded(epic.labels)]

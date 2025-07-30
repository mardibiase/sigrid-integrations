#!/usr/bin/env python3

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

import itertools
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from argparse import ArgumentParser
from datetime import datetime

from issue_data import Epic, Issue, IssueTrackerData, LabelEvent
from issue_utils import anonymize, parseDate, serialize


def sendRequest(url):
    try:
        request = urllib.request.Request(f"{url}")
        request.add_header("PRIVATE-TOKEN", os.environ["GITLAB_API_TOKEN"])
        with urllib.request.urlopen(request) as response:
            yield json.loads(response.read().decode("utf8"))
    except urllib.error.HTTPError as e:
        print(f"Warning: Cannot access {url}, HTTP status {e.code}")


def sendMultipartRequest(url):
    for page in itertools.count(start=1):
        request = urllib.request.Request(f"{url}&page={page}&per_page=100")
        request.add_header("PRIVATE-TOKEN", os.environ["GITLAB_API_TOKEN"])
        with urllib.request.urlopen(request) as response:
            yield from json.loads(response.read().decode("utf8"))
            if not response.headers.get("X-Next-Page"):
                break


def fetchIssues(baseURL, groups, projects):
    for group in groups:
        slug = urllib.parse.quote_plus(group)
        for issue in sendMultipartRequest(f"{baseURL}/api/v4/groups/{slug}/issues?scope=all&state=all"):
            labelHistory = list(fetchIssueLabelHistory(baseURL, issue))
            yield parseIssue(issue, labelHistory)

    for project in projects:
        slug = urllib.parse.quote_plus(project)
        for issue in sendMultipartRequest(f"{baseURL}/api/v4/projects/{slug}/issues?scope=all&state=all"):
            labelHistory = list(fetchIssueLabelHistory(baseURL, issue))
            yield parseIssue(issue, labelHistory)


def parseIssue(issue, labelHistory):
    return Issue(
        id=issue["id"],
        project=issue["references"]["full"].split("#")[0],
        title=issue["title"],
        created=parseDate(issue["created_at"]),
        closed=parseDate(issue["closed_at"]),
        author=anonymize(issue["author"]["name"]),
        assignee=anonymize(issue["assignee"]["name"]) if issue["assignee"] else None,
        epicId=f"{issue['epic']['group_id']}::{issue['epic']['id']}" if issue["epic"] else None,
        labels=issue["labels"],
        labelHistory=labelHistory
    )


def fetchIssueLabelHistory(baseURL, issue):
    labelURL = f"{baseURL}/api/v4/projects/{issue['project_id']}/issues/{issue['iid']}/resource_label_events?t"

    for event in sendMultipartRequest(labelURL):
        if event["action"] == "add" and event["label"]:
            yield LabelEvent(parseDate(event["created_at"]), event["label"]["name"])

            
def fetchEpics(baseURL, issues):
    epicIds = set(issue.epicId for issue in issues if issue.epicId)
    for epicId in epicIds:
        groupId, id = epicId.split("::")
        for epic in sendRequest(f"{baseURL}/api/v4/groups/{groupId}/epics/{id}"):
            yield Epic(
                id=epicId,
                title=epic["title"],
                created=parseDate(epic["created_at"]),
                closed=parseDate(epic["closed_at"]),
                labels=epic["labels"],
                labelHistory=list(fetchEpicLabelHistory(baseURL, epicId))
            )


def fetchEpicLabelHistory(baseURL, epicId):
    groupId, id = epicId.split("::")
    for event in sendMultipartRequest(f"{baseURL}/api/v4/groups/{groupId}/epics/{id}/resource_label_events?t"):
        if event["action"] == "add" and event["label"]:
            yield LabelEvent(parseDate(event["created_at"]), event["label"]["name"])

    
def exportGitLabIssues(baseURL, groups, projects):
    issues = list(fetchIssues(baseURL, groups, projects))
    epics = list(fetchEpics(baseURL, issues))
    return IssueTrackerData("GitLab", datetime.now(), issues, epics)


if __name__ == "__main__":
    parser = ArgumentParser(description="Exports GitLab issues into a format that can be analyzed by Sigrid.")
    parser.add_argument("--gitlab-base-url", type=str, required=True, help="GitLab base URL.")
    parser.add_argument("--group", type=str, default="", help="Comma-separated list of GitLab group paths.")
    parser.add_argument("--project", type=str, default="", help="Comma-separated list of GitLab project paths.")
    parser.add_argument("--out", type=str, default=".sigrid/gitlab-issues.json", help="Output file.")
    args = parser.parse_args()

    if not "GITLAB_API_TOKEN" in os.environ:
        print("Missing environment variable GITLAB_API_TOKEN")
        sys.exit(1)

    groups = args.group.split("," if args.group else None)
    projects = args.project.split("," if args.project else None)
    
    data = exportGitLabIssues(args.gitlab_base_url, groups, projects)
    outputFile = os.path.expanduser(args.out)
    serialize(data, outputFile)
    print(f"Exported {len(data.issues)} issues to {outputFile}")

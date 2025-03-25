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
import urllib.parse
import urllib.request
from argparse import ArgumentParser


def fetchIssues(baseURL, entity, slug):
    for page in itertools.count(start=1):
        url = f"{baseURL}/api/v4/{entity}/{slug}/issues?scope=all&state=all&page={page}&per_page=100"
        request = urllib.request.Request(url)
        request.add_header("PRIVATE-TOKEN", os.environ["GITLAB_API_TOKEN"])
        with urllib.request.urlopen(request) as response:
            yield from json.loads(response.read().decode("utf8"))
            if not response.headers.get("X-Next-Page"):
                break


if __name__ == "__main__":
    parser = ArgumentParser(description="Exports GitLab issues into a format that can be analyzed by Sigrid.")
    parser.add_argument("--gitlab-base-url", type=str, required=True, help="GitLab base URL.")
    parser.add_argument("--group", type=str, default="", help="Comma-separated list of GitLab group paths.")
    parser.add_argument("--project", type=str, default="", help="Comma-separated list of GitLab project paths.")
    parser.add_argument("--out", type=str, default=".sigrid", help="Output directory.")
    args = parser.parse_args()

    if not "GITLAB_API_TOKEN" in os.environ:
        print("Missing environment variable GITLAB_API_TOKEN")
        sys.exit(1)

    issues = []
    for group in args.group.split("," if args.group else None):
        issues += list(fetchIssues(args.gitlab_base_url, "groups", urllib.parse.quote_plus(group)))
    for project in args.project.split("," if args.project else None):
        issues += list(fetchIssues(args.gitlab_base_url, "projects", urllib.parse.quote_plus(project)))

    outputDir = os.path.expanduser(args.out)
    os.makedirs(outputDir, exist_ok=True)
    outputFile = f"{outputDir}/gitlab-issues.json"

    with open(outputFile, "w", encoding="utf8") as f:
        issueData = {"issues" : issues}
        json.dump(issueData, f, indent=4)

    print(f"Exported issue data to {outputFile}")

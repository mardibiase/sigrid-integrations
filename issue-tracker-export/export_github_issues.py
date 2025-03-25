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
import re
import sys
import urllib.parse
import urllib.request
from argparse import ArgumentParser


def fetchIssues(apiBaseURL, org, repo):
    url = f"{apiBaseURL}/repos/{org}/{repo}/issues"
    while url is not None:
        request = urllib.request.Request(url)
        request.add_header("Authorization", f"Bearer: {os.environ['GITHUB_API_TOKEN']}")
        with urllib.request.urlopen(request) as response:
            yield from json.loads(response.read().decode("utf8"))
            link = re.compile("<(\\S+?)>; rel=\"next\"").search(response.headers.get("link", ""))
            url = link.group(1) if link else None


if __name__ == "__main__":
    parser = ArgumentParser(description="Exports GitHub issues into a format that can be analyzed by Sigrid.")
    parser.add_argument("--github-api-url", type=str, default="https://api.github.com")
    parser.add_argument("--org", type=str, required=True, help="GitHub organization name.")
    parser.add_argument("--repo", type=str, required=True, help="Comma-separated list of GitHub repository names.")
    parser.add_argument("--out", type=str, default=".sigrid", help="Output directory.")
    args = parser.parse_args()

    if not "GITHUB_API_TOKEN" in os.environ:
        print("Missing environment variable GITHUB_API_TOKEN")
        sys.exit(1)

    repoIssues = [list(fetchIssues(args.github_api_url, args.org, repo)) for repo in args.repo.split(",")]
    issues = list(itertools.chain(*repoIssues))

    outputDir = os.path.expanduser(args.out)
    os.makedirs(outputDir, exist_ok=True)
    outputFile = f"{outputDir}/github-issues.json"

    with open(outputFile, "w", encoding="utf8") as f:
        issueData = {"issues" : issues}
        json.dump(issueData, f, indent=4)

    print(f"Exported issue data to {outputFile}")

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

import json
import os
import sys
from dataclasses import dataclass
from datetime import date
from http.client import RemoteDisconnected
from json import JSONDecodeError
from typing import Callable, Any, Union
import urllib.parse
import urllib.request
import urllib.error
from urllib.error import URLError
import logging
from argparse import ArgumentParser

LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class Finding:
    id: str
    href: str
    first_seen_snapshot_date: date
    file_path: str
    start_line: int
    end_line: int
    type: str
    severity: str
    severity_score: float
    status: str
    component: str
    cweId: str

class SigridApiClient:
    
    def __init__(self, customer: str, system: str, token: str):
        self.customer = customer.lower()
        self.system = system.lower()
        self.token = token

    def get_security_findings(self) -> Union[Any, None]:
        try:
            req = urllib.request.Request(f'https://sigrid-says.com/rest/analysis-results/api/v1/security-findings/{self.customer}/{self.system}')
            req.add_header('Authorization', 'Bearer ' + self.token)
            with urllib.request.urlopen(req) as response:
                return json.loads(self.handle_response(response))
        except URLError as e:
            LOG.error('Unable to connect to Sigrid API: %s', str(e))
            return None
        except RemoteDisconnected:
            LOG.error('Sigrid disconnected or timed out')
            return None
        except JSONDecodeError:
            LOG.error('Sigrid API response contains invalid JSON')
            return None

    @staticmethod
    def handle_response(response):
        if response.status == 200:
            findings = response.read().decode('utf-8')
            LOG.info('Sigrid returned JSON (length: %s chars)', len(findings))
            return findings
        else:
            LOG.error('Sigrid returned status code %s', response.status)
            return None

class PolarionApiClient:
    SEVERITY_MAPPING = {
        "critical" : "Must Have",
        "high" : "Should Have",
        "medium" : "Nice to Have",
        "low" : "Nice to Have"
    }

    def __init__(self, baseURL, token, projectId):
        self.baseURL = baseURL
        self.token = token
        self.projectId = urllib.parse.quote(projectId.encode("utf8"))

    def call(self, method, path, body=None):
        data = None if body == None else json.dumps(body).encode("utf8")
    
        try:
            request = urllib.request.Request(f"{self.baseURL}{path}", data=data, method=method)
            request.add_header("Content-Type", "application/json")
            request.add_header("Accept", "application/json")
            request.add_header("Authorization", f"Bearer {self.token}")
            response = json.loads(urllib.request.urlopen(request).read().decode("utf-8"))
            return response
        except urllib.error.HTTPError as e:
            print("-" * 80)
            print(f"Polarion API failed with HTTP status {e.status} for {path}")
            print("-" * 80)
            print(e.read().decode("utf8"))
     
    def listWorkItems(self):
        return self.call("GET", f"/projects/{self.projectId}/workitems")
        
    def checkWorkItemExists(self, fingerprint):
        encodedFingerprint = urllib.parse.quote(fingerprint.encode("utf8"))
        response = self.call("GET", f"/projects/{self.projectId}/workitems?query=fingerprint%3A{encodedFingerprint}")
        return "data" in response and len(response["data"]) > 0
        
    def createWorkItems(self, workItems):
        body = {"data" : workItems}
        return self.call("POST", f"/projects/{self.projectId}/workitems", body)
        
    def linkWorkItems(self, workItemId, links):
        body = {"data" : links}
        return self.call("POST", f"/projects/{self.projectId}/workitems/{workItemId}/linkedworkitems", body)

    def create_work_item(self, finding: Finding):
        if finding.status == "RAW":
            return {
                        "type": "workitems",
                        "attributes": {
                            "title": f"Sigrid - {finding.type}",
                            "type": "sigridsecurityissue",
                            "priority": str(finding.severity_score*10),
                            "description": {
                                "type": "text/html",
                                "value": f"Sigrid security finding: {finding}"
                            },
                            "hyperlinks": [
                            {
                                "role": "ref_ext",
                                "uri": finding.href
                            }
                            ],
                            "severity": self.SEVERITY_MAPPING[finding.severity.lower()],
                            "status": "open",
                            "Fingerprint": str(hash(finding)),
                            "CWE": finding.cweId,
                            "Finding Id": finding.id
                        },
                        "relationships" : {}
                    }
        else:
            return None


def process_findings(findings: Any, include: Callable[[Finding], bool]) -> list[Finding]:
    result = []
    for raw_finding in findings:
        finding = Finding(
            id=raw_finding['id'],
            href=raw_finding['href'],
            first_seen_snapshot_date=date.fromisoformat(raw_finding['firstSeenSnapshotDate']),
            file_path=raw_finding['filePath'],
            start_line=raw_finding['startLine'],
            end_line=raw_finding['endLine'],
            type=raw_finding['type'],
            severity=raw_finding['severity'],
            severity_score=raw_finding['severityScore'],
            status=raw_finding['status'],
            component=raw_finding['component'],
            cweId=raw_finding['cweId']
        )
        if include(finding):
            result.append(finding)
    if len(result) == 0:
        return result
    else:
        return sorted(result, key=lambda x: (x.severity_score, x.first_seen_snapshot_date), reverse=True)


def get_filename(file_path: Union[str, None]) -> str:
    if not file_path:
        return ''
    else:
        if file_path.endswith('/'):
            file_path = file_path[:-1]
        parts = file_path.split('/')
        return parts[-1]


if __name__ == "__main__":
    parser = ArgumentParser(description='Gets open security findings and post them to Slack.')
    parser.add_argument('--customer', type=str, required=True, help="Name of your organization's Sigrid account.")
    parser.add_argument('--system', type=str, required=True, help='Name of your system in Sigrid, letters/digits/hyphens only.')
    parser.add_argument('--polarionproject', type=str, required=True, help='Id of your project in Polation.')
    args = parser.parse_args()

    if sys.version_info.major == 2 or sys.version_info.minor < 9:
        print('Sigrid CI requires Python 3.9 or higher')
        sys.exit(1)

    sigrid_authentication_token = os.getenv('SIGRID_CI_TOKEN')
    if not sigrid_authentication_token:
        print('Missing or incomplete environment variable SIGRID_CI_TOKEN')
        sys.exit(1)

    polarion_authentication_token = os.getenv('POLARION_API_TOKEN')
    if not polarion_authentication_token:
        print('Missing or incomplete environment variable POLARION_API_TOKEN')
        sys.exit(1)

    logging.basicConfig(encoding='utf-8', level=logging.INFO)

    sigrid = SigridApiClient(args.customer, args.system, sigrid_authentication_token)
    all_security_findings = process_findings(sigrid.get_security_findings(), lambda x: True)[0:1]
    print(sigrid.get_security_findings()[0])

    polarionURL = "https://industry-solutions.polarion.com/polarion/rest/v1"
    polarion = PolarionApiClient(polarionURL, polarion_authentication_token, args.polarionproject)

    polarion.createWorkItems(list(map(polarion.create_work_item, all_security_findings)))
    # print(polarion.listWorkItems())

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
from datetime import date, timedelta
from http.client import RemoteDisconnected
from json import JSONDecodeError
from typing import Callable, Any, Union
from urllib import request
from urllib.error import URLError
import logging
from argparse import ArgumentParser, BooleanOptionalAction

LOG = logging.getLogger(__name__)


@dataclass
class Finding:
    href: str
    first_seen_snapshot_date: date
    file_path: str
    start_line: int
    end_line: int
    type: str
    severity: str
    severity_score: float
    status: str


class SigridApiClient:

    def __init__(self, customer: str, system: str, token: str):
        self.customer = customer.lower()
        self.system = system.lower()
        self.token = token

    def get_security_findings(self) -> Union[Any, None]:
        try:
            req = request.Request(f'https://sigrid-says.com/rest/analysis-results/api/v1/security-findings/{self.customer}/{self.system}')
            req.add_header('Authorization', 'Bearer ' + self.token)
            with request.urlopen(req) as response:
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

    @staticmethod
    def is_valid_token(token):
        return token is not None and len(token) >= 64

class PolarionApiClient:

    def __init__(self, projectid: str, token: str):
        self.token = token
        self.projectid = projectid
    
    def retreive(self):
        try:
            req = request.Request(f"https://industry-solutions.polarion.com/polarion/rest/v1/projects/{self.projectid}/workitems")
            req.add_header('Authorization', 'Bearer ' + self.token)
            with request.urlopen(req) as response:
                return json.loads(self.handle_response(response))
        except URLError as e:
            LOG.error('Unable to connect to Polarion API: %s', str(e))
            return None
        except RemoteDisconnected:
            LOG.error('Polarion disconnected or timed out')
            return None
        except JSONDecodeError:
            LOG.error('Polarion API response contains invalid JSON')
            return None

    def post(self, data):
        try:
            req = request.Request(f"https://industry-solutions.polarion.com/polarion/rest/v1/projects/{self.projectid}/workitems", data=data, method="POST")
            req.add_header('Authorization', 'Bearer ' + self.token)
            req.add_header('Content-Type', 'application/json')
            with request.urlopen(req) as response:
                return json.loads(self.handle_response(response))
        except URLError as e:
            LOG.error('Unable to connect to Polarion API: %s', str(e))
            return None
        except RemoteDisconnected:
            LOG.error('Polarion disconnected or timed out')
            return None
        except JSONDecodeError:
            LOG.error('Polarion API response contains invalid JSON')
            return None


    @staticmethod
    def handle_response(response):
        if response.status == 200:
            res = response.read().decode('utf-8')
            LOG.info('[200] Polarion returned JSON (length: %s chars)', len(res))
            return res
        elif response.status == 201:
            res = response.read()
            LOG.info('[201] Polarion returned JSON (length: %s chars)', len(res))
            return res
        else:
            LOG.error('Polarion returned status code %s', response.status)
            return None
        
    @staticmethod
    def is_valid_token(token):
        return token is not None

def filter_finding(finding: Finding) -> bool:
    return True


def process_findings(findings: Any, include: Callable[[Finding], bool]) -> list[Finding]:
    result = []
    for raw_finding in findings:
        print(raw_finding)
        finding = Finding(
            raw_finding['href'],
            date.fromisoformat(raw_finding['firstSeenSnapshotDate']),
            raw_finding['filePath'],
            raw_finding['startLine'],
            raw_finding['endLine'],
            raw_finding['type'],
            raw_finding['severity'],
            raw_finding['severityScore'],
            raw_finding['status']
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


def createWorkItem(finding: Finding):
    if finding.status == "RAW":
        return {
                    "type": "workitems",
                    "attributes": {
                        "title": f"Sigrid - {finding.type}",
                        "type": "task",
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
                        "severity": "Normal",
                        "status": "open"
                    }
                }
    else:
        return None

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
    if not SigridApiClient.is_valid_token(sigrid_authentication_token):
        print('Missing or incomplete environment variable SIGRID_CI_TOKEN')
        sys.exit(1)

    polarion_authentication_token = os.getenv('POLARION_API_TOKEN')
    if not PolarionApiClient.is_valid_token(polarion_authentication_token):
        print('Missing or incomplete environment variable POLARION_API_TOKEN')
        sys.exit(1)

    logging.basicConfig(encoding='utf-8', level=logging.INFO)

    sigrid = SigridApiClient(args.customer, args.system, sigrid_authentication_token)
    all_findings = sigrid.get_security_findings()
    processed_findings = process_findings(all_findings, filter_finding)
    print(len(processed_findings))
    print(processed_findings[0])

    polarion = PolarionApiClient(args.polarionproject, polarion_authentication_token)

    polarion_workitems = polarion.retreive()
    print(polarion_workitems["data"])

    workitems_to_add = [createWorkItem(processed_findings[0])]

    # polarion.post(json.dumps({"data": workitems_to_add}).encode('utf-8'))
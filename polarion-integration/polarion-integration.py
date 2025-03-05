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
        self.sigrid_api = f'https://sigrid-says.com/rest/analysis-results/api/v1/security-findings/{customer.lower()}/{system.lower()}'
        self.token = token

    def get_findings(self) -> Union[Any, None]:
        try:
            req = request.Request(self.sigrid_api)
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
            LOG.info('Sigrid returned findings JSON (length: %s chars)', len(findings))
            return findings
        else:
            LOG.error('Sigrid returned status code %s', response.status)
            return None

    @staticmethod
    def is_valid_token(token):
        return token is not None and len(token) >= 64
    

def filter_finding(finding: Finding) -> bool:
    return True


def process_findings(findings: Any, include: Callable[[Finding], bool]) -> list[Finding]:
    result = []
    for raw_finding in findings:
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




if __name__ == "__main__":
    parser = ArgumentParser(description='Gets open security findings and post them to Slack.')
    parser.add_argument('--customer', type=str, required=True, help="Name of your organization's Sigrid account.")
    parser.add_argument('--system', type=str, required=True, help='Name of your system in Sigrid, letters/digits/hyphens only.')
    args = parser.parse_args()

    if sys.version_info.major == 2 or sys.version_info.minor < 9:
        print('Sigrid CI requires Python 3.9 or higher')
        sys.exit(1)

    sigrid_authentication_token = os.getenv('SIGRID_CI_TOKEN')
    if not SigridApiClient.is_valid_token(sigrid_authentication_token):
        print('Missing or incomplete environment variable SIGRID_CI_TOKEN')
        sys.exit(1)

    logging.basicConfig(encoding='utf-8', level=logging.INFO)

    sigrid = SigridApiClient(args.customer, args.system, sigrid_authentication_token)
    all_findings = sigrid.get_findings()
    processed_findings = process_findings(all_findings, filter_finding)
    print(processed_findings)

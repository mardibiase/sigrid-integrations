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
    toolName: str
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
        "CRITICAL" : "Must Have",
        "HIGH" : "Should Have",
        "MEDIUM" : "Nice to Have",
        "LOW" : "Nice to Have"
    }

    def __init__(self, baseURL, token, projectId, systemWorkItemId):
        self.baseURL = baseURL
        self.token = token
        self.projectId = urllib.parse.quote(projectId.encode("utf8"))
        self.systemWorkItemId = systemWorkItemId

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
    
    def is_new_finding(self, finding: Finding) -> bool:
        response = self.call("GET", f"/projects/{self.projectId}/workitems?query=findingid%3A{finding.id}")
        return not ("data" in response and len(response["data"]) > 0)

    def get_finding_id(self, finding: Finding) -> str:
        response = self.call("GET", f"/projects/{self.projectId}/workitems?query=findingid%3A{finding.id}")
        return response["data"][0]["id"]

    def is_new_component(self, componentName, componentVersion) -> bool:
        query = f"componentName%3A{componentName}%20AND%20componentVersion%3A{componentVersion}"
        response = self.call("GET", f"/projects/{self.projectId}/workitems?query={query}")
        return not ("data" in response and len(response["data"]) > 0)
    
    def get_component_id(self, componentName, componentVersion) -> str:
        query = f"componentName%3A{componentName}%20AND%20componentVersion%3A{componentVersion}"
        response = self.call("GET", f"/projects/{self.projectId}/workitems?query={query}")
        return response["data"][0]["id"]

    def create_work_items(self, workItems):
        body = {"data" : workItems}
        return self.call("POST", f"/projects/{self.projectId}/workitems", body)

    def create_sbom_component(self, componentName, componentVersion):
        return {
                        "type": "workitems",
                        "attributes": {
                            "title": f"{componentName}-{componentVersion}",
                            "type": "sbomcomponent",
                            "priority": "50", 
                            "description": {
                                "type": "text/html",
                                "value": f""
                            },
                            "componentName": componentName,
                            "componentVersion": componentVersion,
                            "componentPURL": "todo"
                        },
                        "relationships" : {}
                    }


    def create_sbom_security_finding(self, finding: Finding):
        if finding.status == "RAW":
            return {
                        "type": "workitems",
                        "attributes": {
                            "title": f"{finding.type}",
                            "type": "sbomsecurityissue",
                            "priority": "50", # str(finding.severity_score*10),
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
                            "severity": self.SEVERITY_MAPPING[finding.severity],
                            "cwe": finding.cweId,
                            "findingid": finding.id
                        },
                        "relationships" : {}
                    }
        else:
            return None
        
    def link_findings_to_components(self, findings: list[Finding]):
        component_names = list(set(map(lambda x: x.component, findings)))
        component_names = list(map(lambda x: "None" if x is None else x, component_names))
        new_components_names = list(filter(lambda x: self.is_new_component(x, "sigrid"), component_names))
        new_components_workitems = list(map(lambda x: self.create_sbom_component(x, "sigrid"), new_components_names))

        self.create_work_items(new_components_workitems)

        list(map(self.link_component_to_release, new_components_workitems))

        list(map(self.link_finding_to_component, findings))

    def link_component_to_release(self, component):
        component_id = self.get_component_id(component["attributes"]["componentName"], component["attributes"]["componentVersion"]).split("/")[-1]
        self.create_workitem_links(component_id, self.systemWorkItemId, "containedIn")

    def link_finding_to_component(self, finding: Finding):
        finding_id = self.get_finding_id(finding).split("/")[-1]
        component_name = "remainder" if finding.component is None else finding.component
        component_id = self.get_component_id(component_name, "sigrid")
        self.create_workitem_links(finding_id, component_id, "impacts")

    def create_workitem_links(self, fro, to, role):
        body = {"data" : [{
            "type" : "linkedworkitems",
            "attributes" : {
                "role" : role
            },
            "relationships" : {
                "workItem" : {
                    "data" : {
                        "type" : "workitems",
                        "id" : to
                    }
                }
            }
        }]}
        
        return self.call("POST", f"/projects/{self.projectId}/workitems/{fro}/linkedworkitems", body)   

    def filter_security_findings(self, finding: Finding) -> bool:
        return finding.severity != "INFORMATION"
    
    def filter_internal_security_only(self, finding: Finding) -> bool:
        return finding.toolName != "SIG Open Source Health"
    

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
            cweId=raw_finding['cweId'],
            toolName=raw_finding['toolName']
        )
        if include(finding):
            result.append(finding)
    if len(result) == 0:
        return result
    else:
        return sorted(result, key=lambda x: (x.severity_score, x.first_seen_snapshot_date), reverse=True)

if __name__ == "__main__":
    parser = ArgumentParser(description='Gets open security findings and post them to Slack.')
    parser.add_argument('--customer', type=str, required=True, help="Name of your organization's Sigrid account.")
    parser.add_argument('--system', type=str, required=True, help='Name of your system in Sigrid, letters/digits/hyphens only.')
    parser.add_argument('--polarionurl', type=str, required=True, help='Polarion URL. E.g., "https://my-company.polarion.com"')
    parser.add_argument('--polarionproject', type=str, required=True, help='Id of your SBOM project in Polarion.')
    parser.add_argument('--systemworkitem', type=str, required=True, help="All findings will be linked to this workitem. Recommended to be a Release. Formatted as project/workitemid.")
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

    polarionURL = args.polarionurl + "/polarion/rest/v1"
    polarion = PolarionApiClient(polarionURL, polarion_authentication_token, args.polarionproject, args.systemworkitem)

    all_security_findings = process_findings(sigrid.get_security_findings(), polarion.filter_security_findings)

    internal_findings_only = list(filter(polarion.filter_internal_security_only, all_security_findings))

    new_security_findings = list(filter(polarion.is_new_finding, internal_findings_only))
    sbom_findings = list(map(polarion.create_sbom_security_finding, new_security_findings))
    polarion.create_work_items(sbom_findings)

    polarion.link_findings_to_components(new_security_findings)
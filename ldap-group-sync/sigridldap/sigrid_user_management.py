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

import requests
import sys


class SigridUserManagement:
    def __init__(self, sigridURL, customer, token):
        self.sigridURL = sigridURL
        self.customer = customer
        self.token = token

    def callEndPoint(self, method: str, path: str, body=None):
        url = f"{self.sigridURL}{path}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}"
        }

        response = requests.request(method, url, json=body, headers=headers)
        if response.status_code >= 400:
            print(f"Sigrid request to {path} failed with HTTP status {response.status_code}")
            sys.exit(1)
        return response

    def listUserGroups(self):
        response = self.callEndPoint("GET", f"/rest/auth/api/user-management/{self.customer}/groups")
        return response.json()["groups"]

    def createUserGroup(self, name: str):
        response = self.callEndPoint("POST", f"/rest/auth/api/user-management/{self.customer}/groups", {
            "name": name,
            "description": "Sigrid user group created automatically based on LDAP group synchronization.",
            "users": [],
            "systems": []
        })
        return response.json()

    def deleteUserGroup(self, groupId: str):
        return self.callEndPoint("DELETE", f"/rest/auth/api/user-management/{self.customer}/groups/{groupId}")

    def updateGroupMembers(self, groupId: str, userIds: list[str]):
        return self.callEndPoint("PUT", f"/rest/auth/api/user-management/{self.customer}/groups/{groupId}/members", {
            "users": userIds
        })

    def listUsers(self):
        response = self.callEndPoint("GET", f"/rest/auth/api/user-management/{self.customer}/users")
        return response.json()["users"]

    def createUser(self, email: str, firstName: str, lastName: str):
        response = self.callEndPoint("POST", f"/rest/auth/api/user-management/{self.customer}/users", {
            "userInfo": {
                "firstName": firstName,
                "lastName": lastName,
                "emailAddress": email
            },
            "isSSO": True
        })
        return response.json()

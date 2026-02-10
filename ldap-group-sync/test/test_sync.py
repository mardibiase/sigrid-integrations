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

import ldap

from sigridldap.ldap_connection import LdapConfig, LdapConnection
from sigridldap.sigrid_user_management import SigridUserManagement
from sigridldap.sync import syncUserGroups


OPEN_SOURCE_LDAP_CONFIG = LdapConfig(
    url="ldap://ldap.forumsys.com:389",
    bindDN="cn=read-only-admin,dc=example,dc=com",
    bindPassword="password",
    userDN="dc=example,dc=com",
    userQuery="objectclass=inetOrgPerson",
    groupDN="dc=example,dc=com",
    groupQuery="objectclass=groupOfUniqueNames"
)


def testConnectLDAP():
    connection = LdapConnection(OPEN_SOURCE_LDAP_CONFIG).connection
    users = connection.search_s(OPEN_SOURCE_LDAP_CONFIG.bindDN, ldap.SCOPE_SUBTREE, "objectclass=*")

    assert len(users) == 1
    assert users[0][1]["cn"][0].decode("utf8") == "read-only-admin"
    assert users[0][1]["sn"][0].decode("utf8") == "Read Only Admin"


def testCreateMissingGroups():
    sigrid = MockSigridUserManagement()
    ldapConnection = LdapConnection(OPEN_SOURCE_LDAP_CONFIG)
    syncUserGroups(sigrid, ldapConnection)

    assert sigrid.actions == [
        "list groups",
        "create group Mathematicians",
        "create group Scientists",
        "create group Italians",
        "create group Chemists"
    ]


def testDoNotCreateGroupsAlreadyThere():
    sigrid = MockSigridUserManagement()
    sigrid.existingGroups.append({"id": "1", "name": "Mathematicians"})
    sigrid.existingGroups.append({"id": "2", "name": "Scientists"})
    ldapConnection = LdapConnection(OPEN_SOURCE_LDAP_CONFIG)
    syncUserGroups(sigrid, ldapConnection)

    assert sigrid.actions == [
        "list groups",
        "create group Italians",
        "create group Chemists"
    ]


def testDeleteObsoleteGroups():
    sigrid = MockSigridUserManagement()
    sigrid.existingGroups.append({"id": "1", "name": "Mathematicians"})
    sigrid.existingGroups.append({"id": "2", "name": "Scientists"})
    sigrid.existingGroups.append({"id": "3", "name": "Belgians"})
    ldapConnection = LdapConnection(OPEN_SOURCE_LDAP_CONFIG)
    syncUserGroups(sigrid, ldapConnection)

    assert sigrid.actions == [
        "list groups",
        "create group Italians",
        "create group Chemists",
        "delete group Belgians"
    ]


def testAddMissingUsers():
    pass #TODO


def testRetainExistingUsers():
    pass #TODO


def testRemoveUsersNoLongerThere():
    pass #TODO


class MockSigridUserManagement(SigridUserManagement):
    def __init__(self):
        super().__init__("https://dummy", "example", "token")
        self.existingGroups = []
        self.actions = []

    def listUserGroups(self):
        self.actions.append("list groups")
        return self.existingGroups

    def createUserGroup(self, name: str):
        self.actions.append(f"create group {name}")
        groupObject = {
            "id": str(len(self.existingGroups) + 1),
            "name": name
        }
        self.existingGroups.append(groupObject)
        return groupObject

    def deleteUserGroup(self, groupId: str):
        self.actions.append(f"delete group {groupId}")
        self.existingGroups = [group for group in self.existingGroups if group["id"] != groupId]

    def updateGroupMembers(self, groupId: str, userIds: list[str]):
        self.actions.append(f"update group {groupId}")
        pass

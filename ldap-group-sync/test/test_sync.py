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
    userNameAttr="cn",
    userEmailAttr="mail",
    groupDN="dc=example,dc=com",
    groupQuery="objectclass=groupOfUniqueNames",
    groupNameAttr="cn"
)


# We reuse the same LDAP connection across all tests, since
# our LDAP access is read-only anyway.
ldapConnection = LdapConnection(OPEN_SOURCE_LDAP_CONFIG)


def testConnectLDAP():
    connection = ldapConnection.connection
    users = connection.search_s(OPEN_SOURCE_LDAP_CONFIG.bindDN, ldap.SCOPE_SUBTREE, "objectclass=*")

    assert len(users) == 1
    assert users[0][1]["cn"][0].decode("utf8") == "read-only-admin"
    assert users[0][1]["sn"][0].decode("utf8") == "Read Only Admin"


def testCreateMissingGroups():
    sigrid = MockSigridUserManagement()
    syncUserGroups(sigrid, ldapConnection, memberships=False)

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
    sigrid.existingGroups.append({"id": "3", "name": "Chemists"})

    syncUserGroups(sigrid, ldapConnection, memberships=False)

    assert sigrid.actions == [
        "list groups",
        "create group Italians"
    ]


def testDeleteObsoleteGroups():
    sigrid = MockSigridUserManagement()
    sigrid.existingGroups.append({"id": "1", "name": "Mathematicians"})
    sigrid.existingGroups.append({"id": "2", "name": "Scientists"})
    sigrid.existingGroups.append({"id": "3", "name": "Belgians"})

    syncUserGroups(sigrid, ldapConnection, memberships=False)

    assert sigrid.actions == [
        "list groups",
        "create group Italians",
        "create group Chemists",
        "delete group Belgians"
    ]


def testCreateNewUsers():
    sigrid = MockSigridUserManagement()
    sigrid.existingGroups.append({"id": "1", "name": "Mathematicians"})
    sigrid.existingGroups.append({"id": "2", "name": "Scientists"})
    sigrid.existingGroups.append({"id": "3", "name": "Chemists"})

    syncUserGroups(sigrid, ldapConnection)

    assert sigrid.actions == [
        "list groups",
        "create group Italians",
        "create user newton@ldap.forumsys.com",
        "create user einstein@ldap.forumsys.com",
        "create user tesla@ldap.forumsys.com",
        "create user galileo@ldap.forumsys.com",
        "create user euler@ldap.forumsys.com",
        "create user gauss@ldap.forumsys.com",
        "create user riemann@ldap.forumsys.com",
        "create user euclid@ldap.forumsys.com",
        "create user curie@ldap.forumsys.com",
        "create user nobel@ldap.forumsys.com",
        "create user boyle@ldap.forumsys.com",
        "create user pasteur@ldap.forumsys.com",
        "create user nogroup@ldap.forumsys.com"
    ]


def testRetainExistingUsers():
    sigrid = MockSigridUserManagement()
    sigrid.existingGroups.append({"id": "1", "name": "Mathematicians"})
    sigrid.existingGroups.append({"id": "2", "name": "Scientists"})
    sigrid.existingGroups.append({"id": "3", "name": "Chemists"})
    sigrid.existingUsers.append({"id": "1", "email": "tesla@ldap.forumsys.com"})
    sigrid.existingUsers.append({"id": "2", "email": "galileo@ldap.forumsys.com"})
    sigrid.existingUsers.append({"id": "3", "email": "euler@ldap.forumsys.com"})
    sigrid.existingUsers.append({"id": "4", "email": "gauss@ldap.forumsys.com"})
    sigrid.existingUsers.append({"id": "5", "email": "riemann@ldap.forumsys.com"})
    sigrid.existingUsers.append({"id": "6", "email": "euclid@ldap.forumsys.com"})
    sigrid.existingUsers.append({"id": "7", "email": "curie@ldap.forumsys.com"})
    sigrid.existingUsers.append({"id": "8", "email": "nobel@ldap.forumsys.com"})
    sigrid.existingUsers.append({"id": "9", "email": "boyle@ldap.forumsys.com"})
    sigrid.existingUsers.append({"id": "10", "email": "pasteur@ldap.forumsys.com"})
    sigrid.existingUsers.append({"id": "11", "email": "nogroup@ldap.forumsys.com"})

    syncUserGroups(sigrid, ldapConnection)

    assert sigrid.actions == [
        "list groups",
        "create group Italians",
        "create user newton@ldap.forumsys.com",
        "create user einstein@ldap.forumsys.com"
    ]


def testAddMissingUsersToGroup():
    sigrid = MockSigridUserManagement()
    sigrid.existingGroups.append({"id": "1", "name": "Mathematicians"})
    sigrid.existingGroups.append({"id": "2", "name": "Scientists"})
    sigrid.existingGroups.append({"id": "3", "name": "Chemists"})
    sigrid.existingUsers.append({"id": "1", "email": "tesla@ldap.forumsys.com"})
    sigrid.existingUsers.append({"id": "2", "email": "galileo@ldap.forumsys.com"})
    sigrid.existingUsers.append({"id": "3", "email": "euler@ldap.forumsys.com"})
    sigrid.existingUsers.append({"id": "4", "email": "gauss@ldap.forumsys.com"})
    sigrid.existingUsers.append({"id": "5", "email": "riemann@ldap.forumsys.com"})
    sigrid.existingUsers.append({"id": "6", "email": "euclid@ldap.forumsys.com"})
    sigrid.existingUsers.append({"id": "7", "email": "curie@ldap.forumsys.com"})
    sigrid.existingUsers.append({"id": "8", "email": "nobel@ldap.forumsys.com"})
    sigrid.existingUsers.append({"id": "9", "email": "boyle@ldap.forumsys.com"})
    sigrid.existingUsers.append({"id": "10", "email": "pasteur@ldap.forumsys.com"})
    sigrid.existingUsers.append({"id": "11", "email": "nogroup@ldap.forumsys.com"})
    sigrid.existingUsers.append({"id": "12", "email": "newton@ldap.forumsys.com"})
    sigrid.existingUsers.append({"id": "13", "email": "einstein@ldap.forumsys.com"})

    syncUserGroups(sigrid, ldapConnection)

    assert sigrid.actions == [
        "list groups",
        "create group Italians",
        "create user newton@ldap.forumsys.com",
        "create user einstein@ldap.forumsys.com"
    ]


def testRemoveUsersFromGroup():
    pass #TODO


class MockSigridUserManagement(SigridUserManagement):
    def __init__(self):
        super().__init__("https://dummy", "example", "token")
        self.existingGroups = []
        self.existingUsers = []
        self.actions = []

    def listUserGroups(self):
        self.actions.append("list groups")
        return self.existingGroups

    def createUserGroup(self, name: str):
        self.actions.append(f"create group {name}")
        groupObject = {
            "id": str(len(self.existingGroups) + 1),
            "name": name,
            "users": []
        }
        self.existingGroups.append(groupObject)
        return groupObject

    def deleteUserGroup(self, groupId: str):
        self.actions.append(f"delete group {groupId}")
        self.existingGroups = [group for group in self.existingGroups if group["id"] != groupId]

    def updateGroupMembers(self, groupId: str, userIds: list[str]):
        self.actions.append(f"update group {groupId} to {userIds}")
        groupObject = next(group for group in self.existingGroups if group["id"] == groupId)
        groupObject["users"] = userIds

    def listUsers(self):
        return self.existingUsers

    def createUser(self, email: str, firstName: str, lastName: str):
        self.actions.append(f"create user {email}")
        userObject = {
            "id": str(len(self.existingUsers) + 1),
            "email": email,
            "firstName": firstName,
            "lastName": lastName
        }
        self.existingUsers.append(userObject)
        return userObject

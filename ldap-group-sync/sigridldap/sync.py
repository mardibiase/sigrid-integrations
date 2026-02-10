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

from typing import Iterator

from .sigrid_user_management import SigridUserManagement
from .ldap_connection import LdapConnection, LdapGroup, LdapUser


def syncUserGroups(sigrid: SigridUserManagement, ldapConnection: LdapConnection, memberships=True) -> None:
    ldapGroups = ldapConnection.listGroups()
    sigridGroups = {group["name"]: group for group in sigrid.listUserGroups()}

    for group in findMissingGroups(ldapGroups, sigridGroups):
        print(f"Creating Sigrid user group '{group.name}'")
        sigridGroups[group.name] = sigrid.createUserGroup(group.name)

    for group in findOrphanGroups(ldapGroups, sigridGroups):
        print(f"Removing Sigrid user group '{group}'")
        sigrid.deleteUserGroup(group)

    if memberships:
        ldapUsers = ldapConnection.listUsers()
        sigridUsers = {user["email"]: user for user in sigrid.listUsers()}

        for ldapUser in findMissingSigridUsers(ldapUsers, sigridUsers):
            print(f"Creating Sigrid user '{ldapUser.email}'")
            sigridUsers[ldapUser.email] = sigrid.createUser(ldapUser.email, ldapUser.firstName, ldapUser.lastName)

        for ldapGroup in ldapGroups:
            userIds = list(matchGroupUserIds(ldapGroup, ldapUsers, sigridUsers))
            print(f"Updating group memberships for group '{ldapGroup.name}' to {userIds}")
            sigrid.updateGroupMembers(sigridGroups[ldapGroup.name]["id"], userIds)


def findMissingGroups(ldapGroups: list[LdapGroup], sigridGroups: dict) -> list[LdapGroup]:
    return [group for group in ldapGroups if group.name not in sigridGroups]


def findOrphanGroups(ldapGroups: list[LdapGroup], sigridGroups: dict) -> list[str]:
    ldapGroupNames = [group.name for group in ldapGroups]
    return [groupName for groupName in sigridGroups if groupName not in ldapGroupNames]


def findMissingSigridUsers(ldapUsers: list[LdapUser], sigridUsers: dict) -> list[LdapUser]:
    return [user for user in ldapUsers if not user.email in sigridUsers]


def matchGroupUserIds(group: LdapGroup, ldapUsers: list[LdapUser], sigridUsers: dict) -> Iterator[str]:
    for uid in group.userIds:
        ldapUser = next((user for user in ldapUsers if user.uid == uid), None)
        if ldapUser is None:
            print(f"Warning: user '{uid}' is a member of group '{group.name}', but found no matching LDAP user")
            continue
        sigridUser = sigridUsers[ldapUser.email]
        if sigridUser is None:
            print(f"Warning: user '{uid}' is a member of group '{group.name}', but found no matching Sigrid user")
            continue
        yield sigridUser["id"]

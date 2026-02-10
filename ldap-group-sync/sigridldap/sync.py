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

from .sigrid_user_management import SigridUserManagement
from .ldap_connection import LdapConnection, LdapGroup


def syncUserGroups(sigrid: SigridUserManagement, ldapConnection: LdapConnection) -> None:
    ldapGroups = {group.name: group for group in ldapConnection.listGroups()}
    sigridGroups = {group["name"]: group for group in sigrid.listUserGroups()}

    createGroups = [group for group in ldapGroups if group not in sigridGroups]
    removeGroups = [group for group in sigridGroups if group not in ldapGroups]

    for group in createGroups:
        print(f"Creating Sigrid user group '{group}'")
        sigridGroups[group] = sigrid.createUserGroup(group)

    for group in removeGroups:
        print(f"Removing Sigrid user group '{group}'")
        sigrid.deleteUserGroup(group)

    for groupName, ldapGroup in ldapGroups.items():
        print(f"Updating group memberships for group '{groupName}'")
        syncGroupMemberships(ldapGroup, sigridGroups[groupName])


def syncGroupMemberships(ldapGroup: LdapGroup, sigridGroup: dict) -> None:
    pass

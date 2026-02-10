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
from dataclasses import dataclass


@dataclass
class LdapConfig:
    url: str
    bindDN: str
    bindPassword: str
    userDN: str
    userQuery: str
    userNameAttr: str
    userEmailAttr: str
    groupDN: str
    groupQuery: str
    groupNameAttr: str


@dataclass
class LdapUser:
    uid: str
    email: str
    firstName: str
    lastName: str


@dataclass
class LdapGroup:
    name: str
    userIds: list[str]


class LdapConnection:
    def __init__(self, config: LdapConfig):
        self.config = config
        self.connection = ldap.initialize(config.url)
        self.connection.simple_bind_s(config.bindDN, config.bindPassword)

    def listUsers(self) -> list[LdapUser]:
        objects = self.connection.search_s(self.config.userDN, ldap.SCOPE_SUBTREE, self.config.userQuery)
        return [self.parseUserObject(object) for object in objects if self.config.userEmailAttr in object[1]]

    def parseUserObject(self, object) -> LdapUser:
        uid = object[0]
        email = object[1][self.config.userEmailAttr][0].decode("utf8")
        name = object[1][self.config.userNameAttr][0].decode("utf8")
        firstName = name.split(" ")[0] if " " in name else name
        lastName = name[len(firstName) + 1:] if " " in name else name
        return LdapUser(uid, email, firstName, lastName)

    def listGroups(self) -> list[LdapGroup]:
        objects = self.connection.search_s(self.config.groupDN, ldap.SCOPE_SUBTREE, self.config.groupQuery)
        return [self.parseGroupObject(object) for object in objects]

    def parseGroupObject(self, object) -> LdapGroup:
        name = object[1][self.config.groupNameAttr][0].decode("utf8")
        userIds = [member.decode("utf8") for member in object[1]["uniqueMember"]]
        return LdapGroup(name, userIds)

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

import os
import sys

from ldap_connection import LdapConfig, LdapConnection, LdapGroup
from sigrid_user_management import SigridUserManagement
from sync import syncUserGroups


def getRequiredEnv(name: str) -> str:
    if name not in os.environ:
        print(f"Missing required environment variable {name}")
        sys.exit(1)
    return os.environ[name]


if __name__ == "__main__":
    sigridURL = os.environ.get("SIGRID_UM_URL", "https://sigrid-says.com")
    token = getRequiredEnv("SIGRID_UM_TOKEN")
    customer = getRequiredEnv("SIGRID_UM_CUSTOMER")
    sigrid = SigridUserManagement(sigridURL, customer, token)

    ldapConfig = LdapConfig(
        url=getRequiredEnv("SIGRID_LDAP_URL"),
        bindDN=getRequiredEnv("SIGRID_LDAP_BIND_DN"),
        bindPassword=getRequiredEnv("SIGRID_LDAP_BIND_PASSWORD"),
        userDN=getRequiredEnv("SIGRID_LDAP_USER_DN"),
        userQuery=getRequiredEnv("SIGRID_LDAP_USER_QUERY"),
        groupDN=getRequiredEnv("SIGRID_LDAP_GROUP_DN"),
        groupQuery=getRequiredEnv("SIGRID_LDAP_GROUP_QUERY")
    )
    ldapConnection = LdapConnection(ldapConfig)

    syncUserGroups(sigrid, ldapConnection)

# Sigrid LDAP group synchronization

Synchronizes between Sigrid user groups and LDAP groups. This includes the following:

- For all LDAP groups, a corresponding Sigrid user group with the same name will be created.
- All users in LDAP groups will be added to the corresponding Sigrid user groups.
- Users that are no longer part of an LDAP group, will be removed from the corresponding Sigrid user group.
- Sigrid user groups for which there is no longer a corresponding LDAP user group will be removed.

The [Sigrid user management API](https://docs.sigrid-says.com/integrations/sigrid-api-documentation.html#user-management)
is used for interaction between these scripts and Sigrid.

## Prerequisites

- You need Python 3.9+
- Install the dependencies: `pip3 install -r requirements.txt --user`
- You need a [Sigrid API token](https://docs.sigrid-says.com/organization-integration/authentication-tokens.html)
  - This token needs to have administrator rights (since user management requires administrator rights)
  - Your Sigrid API token needs to be available to the script via the `SIGRID_CI_TOKEN` environment variable

## Usage

Configuration is done using environment variables:

| Name                        | Example                              | Description                                             |
|-----------------------------|--------------------------------------|---------------------------------------------------------|
| `SIGRID_UM_URL`             | https://sigrid-says.com              | Sigrid base URL.                                        |
| `SIGRID_UM_CUSTOMER`        | mycompany                            | Your Sigrid customer name.                              |
| `SIGRID_UM_TOKEN`           | (token)                              | Sigrid API token with administrator privileges.         |
| `SIGRID_LDAP_URL`           | ldap://ldap.example.com:389          | LDAP URL.                                               |
| `SIGRID_LDAP_BIND_DN`       | cn=read-only-admin,dc=example,dc=com | LDAP DN used for authenticating this integration.       |
| `SIGRID_LDAP_BIND_PASSWORD` | (password)                           | LDAP password used for authenticating this integration. |
| `SIGRID_LDAP_USER_DN`       | dc=example,dc=com                    | Locations of users to sync.                             |
| `SIGRID_LDAP_USER_QUERY`    | objectclass=inetOrgPerson            | Query on user DN to get the list of users.              |
| `SIGRID_LDAP_GROUP_DN`      | dc=example,dc=com                    | Location of groups to sync.                             |
| `SIGRID_LDAP_GROUP_QUERY`   | objectclass=groupOfUniqueNames       | Query on group DN to get the list of groups.            |


Once all environment variables are in place, you can run the integration:

    ./sigridldap/sigrid_ldap_group_sync.py

You would typically run this as a scheduled job, to periodically perform this synchronization. However, it's also 
possible to run this manually or ad-hoc.

**Note on creating new groups:** This integration will create new groups based on your LDAP groups, with the
corresponding users being added to that group. However, these groups will be created without access to any systems, 
since your LDAP does not contain any information or configuration for Sigrid systems. Therefore, after the groups 
have been created, you will need to configure which Sigrid systems are accessible to each group.

## License

Copyright Software Improvement Group

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

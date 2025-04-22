# Sigrid-Polarion Integration
Adds Sigrid security findings to Polarion.

To run, run `./polarion-integration.py` with the following flags:
--customer: Name of the customer in Sigrid
--system: Name of the system in Sigrid
--polarionurl: URL to Polarion, for example https://my-company.polarion.com
--polarionproject: Name of the Polarion project, for example MyProject
--systemworkitem: Workitem ID for the Sigrid system. All security findings will be linked to this workitem. Recommended to be a Release.

In order to run, the SigridCI token and Polarion API token should be stored in environment variables `SIGRID_CI_TOKEN` and `POLARION_API_TOKEN` respectively.

This script only adds non-existing Sigrid security findings to Polarion. It does not yet remove or update workitems. 


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
    
    


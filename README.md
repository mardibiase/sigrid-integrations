# sigrid-integrations

This repo contains useful code we've created to leverage the power of the Sigrid API. The code is provided as-is, so when you use it, sanity-check your results. We do accept pull requests, so don't hesitate to contribute. Given the as-is nature of the repo, code maybe added, changed, removed or restructured as we learn more.

## Usage remarks

- The code is packaged in a Docker image that is available at `softwareimprovementgroup/sigrid-integrations`
- This repo contains a convenience script `integrations.sh` to start a container and provides access to the code that is currenty available
- All available integrations contain a README that describes functionality and usage in more detail.

## Contributing remarks

- Currently, all code is written in Python. This is not a hard rule, but it does make it easier to package it in a Docker image.
- All integrations should
 - contain a README
 - display a usage message when called with no arguments
 - write any output to the current directory if none specified
 - not need to run as root

## Available integrations

- `report-generator`
- `objectives_report.py`
- `get_scope_file.py`

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
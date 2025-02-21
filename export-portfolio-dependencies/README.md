# Export portfolio dependencies to Excel

## Intro

The export portfolio dependencies to Excel is a tiny Python script to export all your Sigrid portfolio dependencies in a single self-contained document.  
Each sheet in the output Excel file will contain a systems' dependencies.

## Status

This tool is currently in the proof-of-concept phase. Things may not completely work yet, or break at a given time. Usage is at your own risk. Please contact the team working on the tool if you have an urgent need, but that there is no official support at this moment.

## Installation

See the Report Generator [installation documents](../report-generator/docs/installation.md) but change the path to the export-portfolio-dependencies one.

## Usage

### Create customer-specific access token

Before using the system, you need to generate a Sigrid token. Tokens are unique **per customer**. Create a new token for a new customer:

1. Go to Sigrid: `https://sigrid-says.com/<your-customer>`
2. Go to user settings, via the person icon on the top right
3. Click "create new token" and create a token with a descriptive name, e.g. `customername-export-portfolio-dependencies`.
4. Save the token somewhere so you don't need to recreate it every time. (Tokens are valid for 1 year)
5. Export the token in your path under the `SIGRID_CI_TOKEN` value. Most likely, something along the lines of `export SIGRID_CI_TOKEN=<token>` 

### Run the tool

* Run: `export_portfolio_dependencies.py [-h] --customer CUSTOMER [--output OUTPUT] [--debug]`

If all goes well, the report should be generated in the folder where you run the command. Otherwise, in the specified path/filename when passing the `--output` parameter.  

#### Troubleshooting

If there is an error and you can't figure out what causes it, run the tool again with the `--debug` parameter appended to gather additional information. Then, open an issue on this repository.

## Suggestions / feedback

Feedback is welcome! If you have ideas to improve this export, please reach out to Software Improvement Group, or open a pull request to this repository.

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
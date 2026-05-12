# Compare Security Findings Between Systems

## Intro

The Compare Security Findings tool is a Python script that compares security findings between two Sigrid systems (typically a main branch and a feature branch) and exports the differences to Excel. The tool identifies raw security findings present in the new system but not in the main system, helping teams understand the security impact of their changes before merging.

The output Excel file contains a sheet with findings that are currently in the stages Raw, Refined or Will Fix. Findings that were either fixed or marked as False Positive/Risk Accepted will not be included in this overview. 

## Status

This tool is currently in the proof-of-concept phase. Things may not completely work yet, or break at a given time. Usage is at your own risk. Please contact the team working on the tool if you have an urgent need, but there is no official support at this moment.

## Installation

1. Clone this repository and `cd` into it.
2. Install the dependencies: `pip3 install -r compare-security-findings/requirements.txt`

Required dependencies:
- `pandas`
- `openpyxl`

Install with: `pip install pandas openpyxl`

## Usage

### Create customer-specific access token

Before using the system, you need to generate a Sigrid token. Tokens are unique **per customer**. Create a new token for a new customer:

1. Go to Sigrid: `https://sigrid-says.com/<your-customer>`
2. Go to user settings, via the person icon on the top right
3. Click "create new token" and create a token with a descriptive name, e.g. `customername-compare-security-findings`
4. Save the token somewhere so you don't need to recreate it every time. (Tokens are valid for 1 year)
5. Export the token in your path under the `SIGRID_CI_TOKEN` value. Most likely, something along the lines of `export SIGRID_CI_TOKEN=<token>` 

### Run the tool

```bash
python compare_security_findings.py --customer CUSTOMER --main-system MAIN_SYSTEM --new-system NEW_SYSTEM [--output OUTPUT] [--token TOKEN] [--debug]
```

**Required arguments:**
- `--customer`: Sigrid customer name
- `--main-system`: The main branch system name (must match the exact 'System name' in Sigrid)
- `--new-system`: The new system/branch name that will be merged into main

**Optional arguments:**
- `--output`: Output Excel file name (not path). If not specified, a default name will be used: `{customer}-{main-system}-{new-system}-security-findings.xlsx`
- `--token`: Sigrid API token. If not provided, uses the `SIGRID_CI_TOKEN` environment variable
- `--line-tolerance`: To override the default line tolerance number for fuzzy match of security findings
- `--debug`: Enable debug logging

**Example:**
```bash
python compare_security_findings.py \
  --customer <portfolio-name> \
  --main-system <system-main> \
  --new-system <system-dev-branch> \
  --output comparison-report.xlsx
```

### How it works

1. **Fetches security findings** from both the main system and new system via the Sigrid API
2. **Compares findings** using exact matching (file path, line numbers, type, and rule ID)
3. **Applies fuzzy matching** for findings that are in the same file but have a slightly different line number to detect findings that may have moved in the code
4. **Identifies new findings** that exist in the new system but not in the main system
5. **Creates an Excel file** with an overview of all raw findings in the new system that do not appear in the main system

#### Fuzzy Matching Logic

When code changes occur above a security finding, the line numbers shift but the actual vulnerability remains the same. To help identify these cases, the tool uses a two-tier matching approach:

1. **Exact Match**: First attempts to match findings using all properties including line numbers (file path + start line + end line + type + rule ID)
2. **Fuzzy Match**: If no exact match is found, checks if a similar finding exists in the same file with the same characteristics but different line numbers (file path + type + CWE ID + rule ID)
   - Only matches if the finding is within ±50 lines of its potential match
   - This helps identify findings that moved due to code insertions/deletions above them

When a fuzzy match is found, the finding is still reported as "new" (since we can never be sure if it moved without looking at the code), but the Excel output includes additional columns showing the potential matching finding in the main system.

This allows reviewers to quickly determine if a "new" finding is truly new or just a moved existing finding.

#### Excel Output

The Excel output includes comprehensive information for each finding:
- Finding ID and Sigrid URL
- File path and line numbers
- Finding type and severity
- CWE ID and categories
- Timestamps (first seen, last seen)
- Fuzzy match information (if applicable)

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

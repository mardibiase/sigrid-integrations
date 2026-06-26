# Post security findings to Microsoft Teams

This directory contains a Python script illustrating how Sigrid's REST API can be used to send a daily report about new security findings to Microsoft Teams.

At the highest level, this script carries out 3 steps and then finishes:

1. Use the [appropriate endpoint](https://docs.sigrid-says.com/integrations/sigrid-api-documentation.html#security-and-reliability-findings) in Sigrid's REST API to get the current open findings for the given system.
2. Compose a message listing the latest 5 findings, ordered by decreasing severity.
3. Send this message to Teams by making an HTTP POST request to a Teams webhook.

## Usage

(setup steps and screenshots go here)

## Usage

The idea is to use this script for instance once per day as a scheduled job, the same as the Slack version.

### Prerequisites

- You need a [Sigrid authentication token](https://docs.sigrid-says.com/organization-integration/authentication-tokens.html).
- You need to create a Teams webhook (see below).

### Step 1: Create a webhook in Microsoft Teams

> Note: Microsoft has deprecated the old "Incoming Webhook" connector. Use the **Workflows app** instead.

1. In Teams, go to the channel where you want alerts posted.
2. Click **"..." (more options)** next to the channel name.
3. Select **Workflows**.

   <img width="330" height="362" alt="teams-workflow" src="https://github.com/user-attachments/assets/44ba9cb2-1a3b-44af-bfbb-398ec5bc1f75" />

4. Search for and select the template **"Send webhook alerts to a channel"**.

   <img width="720" height="388" alt="teams-send-webhook" src="https://github.com/user-attachments/assets/9b101b2b-719c-44db-8b47-965caf60ec31" />

5. Confirm the team and channel, then **Save**.

   <img width="661" height="568" alt="teams-channel" src="https://github.com/user-attachments/assets/fbdbceb5-ffa5-4a59-bf0b-dbd4c60cd1a2" /> 
  
6. Copy the generated webhook URL.


### Step 2: Store secrets in your CI/CD environment

Store both as secrets:
- `SIGRID_CI_TOKEN`: your Sigrid authentication token
- `TEAMS_WEBHOOK`: the webhook URL from Step 1

### Step 3: Add a scheduled job (GitHub Actions example)

```yaml
name: "Teams alerts for Sigrid security findings"
on:
  schedule:
    - cron: "0 6 * * 1-5"
jobs:
  teamsalerts:
    name: "Send Teams alerts"
    runs-on: ubuntu-latest
    steps:
      - name: "Check out repository"
        uses: actions/checkout@v4
      - name: Download Sigrid integrations
        run: "git clone https://github.com/Software-Improvement-Group/sigrid-integrations.git sigrid-integrations"
      - run: "sigrid-integrations/teams-security-findings/daily_findings.py --customer mycustomer --system mysystem"
        env:
          SIGRID_CI_TOKEN: "${{ secrets.SIGRID_CI_TOKEN }}"
          TEAMS_WEBHOOK: "${{ secrets.TEAMS_WEBHOOK }}"
```

Replace `mycustomer` and `mysystem` with your Sigrid customer account name and system name.

### Example result

<img width="675" height="314" alt="teams-findings" src="https://github.com/user-attachments/assets/83059a1e-d5a0-47d9-8589-34c449b7a769" />

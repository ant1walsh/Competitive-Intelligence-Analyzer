# Daily Competitive Intelligence Agent

A fully automated competitive intelligence pipeline that monitors 29 AI infrastructure competitors daily, synthesizes findings using **GLM-5 on Friendli Serverless Endpoints**, and posts a structured executive brief to Slack every morning at 7 AM.

---

## How It Works

```
competitors.csv  →  SerpAPI (Google News)  →  GLM-5 on Friendli  →  Slack #competitive-intel
```

1. Reads the competitor list from `competitors.csv`
2. Searches Google News for each competitor's developments in the past 24 hours via SerpAPI
3. Sends all results to GLM-5 on Friendli to synthesize an executive brief
4. Posts the report to the `#competitive-intel` Slack channel via webhook

---

## Files

| File | Description |
|------|-------------|
| `daily_competitive_intel.py` | Main agent script |
| `competitors.csv` | Editable list of competitors to monitor |
| `schedule_cron.sh` | Cron job manager (install, remove, run, view logs) |
| `requirements.txt` | Python dependencies |
| `README.md` | This file |

---

## Setup

### 1. Install dependencies

```bash
pip install requests
```

### 2. Set environment variables

Add these to your `~/.zshrc` (Mac) or `~/.bashrc` (Linux):

```bash
export FRIENDLI_API_KEY="your-friendli-token"
export SERPAPI_KEY="your-serpapi-key"
export SLACK_WEBHOOK_URL="your-slack-webhook-url"
```

Then reload:

```bash
source ~/.zshrc
```

### 3. Schedule the daily cron job

```bash
cd ~/competitive-intel
bash schedule_cron.sh install
```

---

## Usage

```bash
# Install the daily 7 AM cron job
bash schedule_cron.sh install

# Run the agent immediately (manual trigger)
bash schedule_cron.sh run

# View current cron jobs
bash schedule_cron.sh list

# Watch the log in real-time
bash schedule_cron.sh view-log

# Remove the cron job
bash schedule_cron.sh remove
```

---

## Managing the Competitor List

Edit `competitors.csv` to add or remove companies — one per row:

```csv
Company Name
Google Vertex
Amazon Bedrock
Your New Competitor
```

Changes take effect on the next run. No code changes needed.

---

## Report Format

Each daily brief includes:

- **Executive Summary** — 2–3 sentences on the day's most important developments
- **Product & Feature Releases** — Grouped by competitor
- **Customer Acquisitions & Case Studies**
- **Partnerships & Integrations**
- **Funding, Investments & M&A**
- **Events & Sponsorships**
- **Key Takeaways & Implications** — 3–5 strategic bullet points
- **Sources** — Include sources for each newly introduced updates in bulleted list

Sections with no news are omitted automatically. If no competitors have news, a short notice is posted instead.

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `FRIENDLI_API_KEY` | Friendli API token (`flp_...`) |
| `SERPAPI_KEY` | SerpAPI key for Google News search |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL |

---

## Model

**GLM-5** (`zai-org/GLM-5`) via [Friendli Serverless Endpoints](https://friendli.ai/products/serverless-endpoints)

GLM-5 is a 744B parameter MoE model from Zhipu AI, ranked #1 on open model human evaluation arenas. It powers all report synthesis in this agent.

---

## Requirements

- Python 3.10+
- `requests` library
- Active accounts with Friendli, SerpAPI, and Slack
- Mac must be awake at 7 AM for cron to fire (see note below)

> **Note:** macOS cron jobs only run when the machine is awake. If your Mac is frequently asleep at 7 AM, consider using `launchd` instead for more reliable scheduling.

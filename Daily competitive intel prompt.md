# Daily Competitive Intelligence Agent

**Task name:** `daily-competitive-intel`
**Schedule:** Every day at 7:00 AM (cron: `0 7 * * *`)
**Slack channel:** #competitive-intel
**LLM:** Qwen3-235B-A22B-Instruct-2507 via Friendli Serverless Endpoints

---

## Architecture

```
competitors.csv  →  SerpAPI (Google News)  →  Qwen3-235B on Friendli  →  Slack webhook
```

The agent is a standalone Python script (`daily_competitive_intel.py`) that:

1. Reads the competitor list from `competitors.csv` (one company per row)
2. Searches Google News for each competitor's developments in the past 24 hours using SerpAPI
3. Sends all raw search results to Qwen3-235B-A22B-Instruct-2507 on Friendli Serverless Endpoints to synthesize a structured executive brief
4. Posts the finished report to #competitive-intel via Slack incoming webhook

If no news is found for any competitor, a short "no developments" notice is posted instead.

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set environment variables

```bash
export FRIENDLI_API_KEY="your-friendli-token"
export SERPAPI_KEY="your-serpapi-key"
export SLACK_WEBHOOK_URL="your-slack-webhook-url"
```

### 3. Place the competitor list

Ensure `competitors.csv` is in the same directory as the script. The CSV has one column with header `Company Name` and one competitor per row. Add or remove rows at any time — changes take effect on the next run.

### 4. Run manually

```bash
python daily_competitive_intel.py
```

### 5. Schedule with cron (daily at 7 AM)

```bash
crontab -e
```

Add this line (adjust paths to match your setup):

```
0 7 * * * cd /path/to/agent && FRIENDLI_API_KEY="..." SERPAPI_KEY="..." SLACK_WEBHOOK_URL="..." /usr/bin/python3 daily_competitive_intel.py >> /var/log/competitive-intel.log 2>&1
```

---

## Report format

The executive brief follows this structure:

- **Executive Summary** — 2–3 sentences on the day's most important developments
- **Product & Feature Releases** — Grouped by competitor
- **Customer Acquisitions & Case Studies**
- **Partnerships & Integrations**
- **Funding, Investments & M&A**
- **Events & Sponsorships**
- **Key Takeaways & Implications** — 3–5 strategic bullet points
- **Sources** — Include sources for each newly introduced updates in bulleted list

Sections with no relevant news are omitted automatically.

---

## Modifying the competitor list

Edit `competitors.csv` to add or remove companies:

```csv
Company Name
Google Vertex
Amazon Bedrock
New Competitor Here
```

No code changes or restarts are needed — the script reads the CSV fresh on every run.

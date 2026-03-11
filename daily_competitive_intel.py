#!/usr/bin/env python3
"""
Daily Competitive Intelligence Agent
=====================================
Reads a competitor list from CSV, searches for recent news via SerpAPI,
synthesizes an executive brief using Qwen3-235B on Friendli Serverless Endpoints,
and posts the report to Slack via incoming webhook.

Environment variables required:
  FRIENDLI_API_KEY   - Friendli API token (flp_...)
  SERPAPI_KEY         - SerpAPI key
  SLACK_WEBHOOK_URL   - Slack incoming webhook URL
"""

import csv
import json
import os
import sys
import datetime
import requests
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
FRIENDLI_BASE_URL = "https://api.friendli.ai/serverless/v1"
FRIENDLI_MODEL = "Qwen/Qwen3-235B-A22B-Instruct-2507"

COMPETITORS_CSV = Path(__file__).parent / "competitors.csv"
DEFAULT_COMPETITORS = [
    "Google Vertex", "Amazon Bedrock", "Microsoft Azure AI", "Together AI",
    "Nebius", "Crusoe", "GMI Cloud", "Atlas Cloud", "Fireworks", "Baseten",
    "Replicate", "Novita AI", "Hyperstack", "DeepInfra", "SiliconFlow",
    "Anyscale", "Parasail", "Clarifai", "Modal", "OpenRouter",
    "Weights & Biases", "Hugging Face", "Mistral", "Groq", "Cerebras",
    "SambaNova", "vLLM", "SGLang", "Nvidia TensorRT",
]

SERPAPI_SEARCH_URL = "https://serpapi.com/search.json"
SLACK_MAX_CHARS = 39000  # Leave buffer under Slack's 40k limit


# ---------------------------------------------------------------------------
# Step 1: Load competitor list
# ---------------------------------------------------------------------------
def load_competitors() -> list[str]:
    """Read competitor names from CSV; fall back to defaults."""
    if COMPETITORS_CSV.exists():
        with open(COMPETITORS_CSV, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)  # skip header
            names = [row[0].strip() for row in reader if row and row[0].strip()]
            if names:
                print(f"[INFO] Loaded {len(names)} competitors from {COMPETITORS_CSV}")
                return names
    print("[WARN] CSV not found or empty — using default competitor list.")
    return DEFAULT_COMPETITORS


# ---------------------------------------------------------------------------
# Step 2: Search for recent news via SerpAPI
# ---------------------------------------------------------------------------
def search_competitor_news(competitor: str, api_key: str) -> list[dict]:
    """Search Google News for a competitor's developments in the past 24h."""
    query = (
        f'"{competitor}" '
        f"(product launch OR feature release OR partnership OR funding OR "
        f"acquisition OR customer OR investment OR event OR sponsorship)"
    )
    params = {
        "engine": "google",
        "q": query,
        "tbm": "nws",          # Google News
        "tbs": "qdr:d",        # Past 24 hours
        "num": 5,
        "api_key": api_key,
    }
    try:
        resp = requests.get(SERPAPI_SEARCH_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("news_results", [])
        return [
            {
                "title": r.get("title", ""),
                "snippet": r.get("snippet", ""),
                "source": r.get("source", ""),
                "link": r.get("link", ""),
                "date": r.get("date", ""),
            }
            for r in results
        ]
    except Exception as e:
        print(f"[ERROR] Search failed for '{competitor}': {e}")
        return []


def gather_all_news(competitors: list[str], api_key: str) -> dict[str, list[dict]]:
    """Search for each competitor and return a map of competitor -> results."""
    all_news: dict[str, list[dict]] = {}
    for comp in competitors:
        print(f"[SEARCH] {comp}...")
        results = search_competitor_news(comp, api_key)
        if results:
            all_news[comp] = results
            print(f"  -> {len(results)} result(s)")
        else:
            print(f"  -> No results")
    return all_news


# ---------------------------------------------------------------------------
# Step 3: Synthesize executive brief via Qwen3 on Friendli
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """\
You are a competitive intelligence analyst. You will receive raw news search \
results about AI infrastructure competitors. Your job is to synthesize them \
into a structured executive brief.

Rules:
- Only include information that is clearly supported by the provided search results.
- Do NOT fabricate or speculate beyond what the sources say.
- If a category has no relevant news, omit that section entirely.
- Keep the tone professional and analytical, written for a strategy/leadership audience.
- Use Slack markdown: *bold* for headers, bullet points for items, and <url|text> for links.
- End with a Sources section listing every URL used.
"""


def build_user_prompt(news: dict[str, list[dict]], date_str: str) -> str:
    """Build the user prompt containing all raw search results."""
    lines = [
        f"Today's date: {date_str}",
        f"Competitors with news: {len(news)}",
        "",
        "--- RAW SEARCH RESULTS ---",
    ]
    for comp, results in news.items():
        lines.append(f"\n== {comp} ==")
        for r in results:
            lines.append(f"  Title: {r['title']}")
            lines.append(f"  Snippet: {r['snippet']}")
            lines.append(f"  Source: {r['source']}")
            lines.append(f"  Link: {r['link']}")
            lines.append(f"  Date: {r['date']}")
            lines.append("")
    lines.append("--- END OF RESULTS ---")
    lines.append("")
    lines.append(
        "Now write the Daily Competitive Intelligence Brief using this format:\n"
        "\n"
        "*Daily Competitive Intelligence Brief — " + date_str + "*\n"
        "\n"
        "*Executive Summary*\n"
        "2-3 sentences on the most important developments and what they signal.\n"
        "\n"
        "*Product & Feature Releases*\n"
        "Group by competitor. What was launched, why it matters.\n"
        "\n"
        "*Customer Acquisitions & Case Studies*\n"
        "Notable customer wins or endorsements.\n"
        "\n"
        "*Partnerships & Integrations*\n"
        "New strategic partnerships or ecosystem plays.\n"
        "\n"
        "*Funding, Investments & M&A*\n"
        "Funding rounds, acquisitions, or major financial moves.\n"
        "\n"
        "*Events & Sponsorships*\n"
        "Conferences, sponsored events, or keynotes.\n"
        "\n"
        "*Key Takeaways & Implications*\n"
        "3-5 bullet points on strategic meaning.\n"
        "\n"
        "*Sources*\n"
        "List all URLs.\n"
        "\n"
        "Omit any section that has no relevant news. Do not invent information."
    )
    return "\n".join(lines)


def generate_brief(news: dict[str, list[dict]], api_key: str) -> str:
    """Call Qwen3 on Friendli to produce the executive brief using streaming."""
    date_str = datetime.date.today().strftime("%B %d, %Y")
    user_prompt = build_user_prompt(news, date_str)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": FRIENDLI_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 4096,
        "stream": True,
    }

    print("[LLM] Sending to Qwen3-235B on Friendli (streaming)...")
    resp = requests.post(
        f"{FRIENDLI_BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        timeout=30,       # connection timeout
        stream=True,
    )
    if resp.status_code != 200:
        print(f"[ERROR] Friendli API returned {resp.status_code}: {resp.text}")
        resp.raise_for_status()

    # Collect streamed chunks
    content_parts = []
    for line in resp.iter_lines(chunk_size=None):
        if not line:
            continue
        decoded = line.decode("utf-8") if isinstance(line, bytes) else line
        if decoded.startswith("data: "):
            decoded = decoded[len("data: "):]
        if decoded.strip() == "[DONE]":
            break
        try:
            chunk = json.loads(decoded)
            delta = chunk["choices"][0].get("delta", {})
            token = delta.get("content", "")
            if token:
                content_parts.append(token)
                print(token, end="", flush=True)
        except (json.JSONDecodeError, KeyError, IndexError):
            continue

    print()  # newline after streamed output
    content = "".join(content_parts)
    print(f"[LLM] Generated {len(content)} characters.")
    return content


# ---------------------------------------------------------------------------
# Step 4: Post to Slack
# ---------------------------------------------------------------------------
def post_to_slack(webhook_url: str, text: str):
    """Post the brief to Slack. Split into thread if too long."""
    if len(text) <= SLACK_MAX_CHARS:
        _slack_post(webhook_url, text)
        print("[SLACK] Posted full brief.")
    else:
        # Split: main brief up to Sources, then Sources in follow-up
        split_marker = "*Sources*"
        if split_marker in text:
            idx = text.index(split_marker)
            main = text[:idx].rstrip()
            sources = text[idx:]
            _slack_post(webhook_url, main + "\n\n_(Sources posted in thread)_")
            _slack_post(webhook_url, sources)
            print("[SLACK] Posted brief + sources in two messages.")
        else:
            # Hard split at character limit
            _slack_post(webhook_url, text[:SLACK_MAX_CHARS])
            _slack_post(webhook_url, text[SLACK_MAX_CHARS:])
            print("[SLACK] Posted brief in two parts.")


def _slack_post(webhook_url: str, text: str):
    """Send a single message to Slack via webhook."""
    resp = requests.post(
        webhook_url,
        json={"text": text},
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"Slack webhook returned {resp.status_code}: {resp.text}"
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    # Load env vars
    friendli_key = os.environ.get("FRIENDLI_API_KEY")
    serpapi_key = os.environ.get("SERPAPI_KEY")
    slack_webhook = os.environ.get("SLACK_WEBHOOK_URL")

    missing = []
    if not friendli_key:
        missing.append("FRIENDLI_API_KEY")
    if not serpapi_key:
        missing.append("SERPAPI_KEY")
    if not slack_webhook:
        missing.append("SLACK_WEBHOOK_URL")
    if missing:
        print(f"[FATAL] Missing environment variables: {', '.join(missing)}")
        sys.exit(1)

    # Step 1: Load competitors
    competitors = load_competitors()
    print(f"[INFO] Tracking {len(competitors)} competitors.\n")

    # Step 2: Search
    news = gather_all_news(competitors, serpapi_key)
    if not news:
        no_news_msg = (
            f"*Daily Competitive Intelligence Brief — "
            f"{datetime.date.today().strftime('%B %d, %Y')}*\n\n"
            f"No significant competitive developments detected in the past 24 hours."
        )
        post_to_slack(slack_webhook, no_news_msg)
        print("[DONE] No news found. Posted quiet-day notice to Slack.")
        return

    # Step 3: Generate brief
    brief = generate_brief(news, friendli_key)

    # Step 4: Post to Slack
    post_to_slack(slack_webhook, brief)
    print("[DONE] Executive brief posted to #competitive-intel.")


if __name__ == "__main__":
    main()

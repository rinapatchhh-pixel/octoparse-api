# Octoparse AgentTools API examples

Example scripts for calling [Octoparse](https://www.octoparse.com/) scraping templates through the **AgentTools API** (`executeTask` → `exportData`).

## What's here

- **`AgentTools-2124-GoogleNews.py`** — runs the [Google News Scraper (Cloud)](https://www.octoparse.com/template/google-news-scraper-cloud) template (id 2124). It starts one cloud task from a Google News search URL, polls until the export is ready, and downloads the results as JSON.

## Prerequisites

- Python 3.8+
- `pip install requests`
- An Octoparse API key (starts with `op_sk_`), created in your [account center](https://www.octoparse.com/console/account-center/api-keys). The free tier includes 2,000 records/week.

## Run it

```bash
export OCTOPARSE_API_KEY="op_sk_your_key"
python3 AgentTools-2124-GoogleNews.py
```

You'll be asked for:

- an **external user ID** — any stable string you pick (e.g. `my-app-user-1`); it just labels which caller/user started the task;
- an **export folder** — press Enter to use the current folder;
- finally, type **`EXECUTE`** to confirm creating the cloud task.

When the run finishes, the script saves `octoparse_export_<taskId>.json`.

## What you get back

Each row has `keyword` (the search URL you sent) and `FollowField`, which is a JSON **string** — parse it to get the article fields:

```json
{
  "Title": "Senate committee set to vote on whether to hold Fauci in contempt of Congress",
  "Source": "NPR",
  "Author": "Eric Mcdaniel",
  "PublishDate": "2026-08-06 07:16:22 UTC",
  "ProjectUrl": "https://www.npr.org/...",
  "Keyword": "\"Vote\" when:1d",
  "Language": "en"
}
```

This Cloud template returns **metadata only — no article body**. To collect the full body text, use the free companion templates:

- [Google News Scraper (by keyword)](https://www.octoparse.com/template/google-news-scraper) — id 1370
- [Google News Scraper (by URL)](https://www.octoparse.com/template/google-news-scraper-by-URL) — id 1747

Each of those opens the article and returns a `NewsText` field with the full body.

## API basics

- Base URL: `https://openapi.octoparse.com`
- Auth: `x-api-key` header (plus `x-external-user-id` on `executeTask`)
- Flow: `executeTask` → poll `exportData` until `status` is `exported`
- Pricing: usage-based, $0.1 / 1,000 lines
- Full reference: <https://www.octoparse.com/docs/en/api-reference>

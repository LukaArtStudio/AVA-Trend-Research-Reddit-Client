# AVA Trend Research — Reddit Client

Small, read-only reference client for the Reddit Data API.

## Purpose

This project is a private/local research client intended to identify **recurring problem signals, unmet software/tool needs, and general tool-development trends** in public Reddit discussions.

It is **not designed to track, collect, copy, monitor, or appropriate ideas, inventions, project concepts, product concepts, or user-specific idea histories** posted by individual Reddit users. The analysis is centered on recurring problem patterns and incoming signals such as:

- repetitive or frustrating tasks,
- gaps in existing software/tools,
- requests for easier ways to complete a task,
- recurring difficulties described across public discussions.

The client is intentionally read-only.

## What it can do

After Reddit explicitly approves the API access request and OAuth credentials are issued, the client can:

- obtain an OAuth application token,
- search public Reddit posts using a user-supplied query,
- read basic public post fields,
- optionally read a small number of public comments for context,
- return the results as JSON to the local process.

## What it does NOT do

The client does not:

- create posts or comments,
- vote,
- send messages,
- follow users,
- access private data,
- build user profiles,
- infer sensitive personal attributes,
- track individual Redditors,
- scrape Reddit HTML,
- bypass CAPTCHA, rate limits, blocks, or access controls,
- redistribute Reddit content as a service,
- train AI/ML models on Reddit data,
- store Reddit credentials in source code.

## Data minimization

The example client requests only fields needed to understand a public problem signal:

- post title,
- limited self-text,
- subreddit,
- creation time,
- permalink,
- score/comment count for basic context,
- selected public comment text when explicitly requested.

The reference implementation does not create a persistent database.

## OAuth and approval

Do **not** use this client against Reddit Data API until Reddit has explicitly approved the intended access.

Credentials are supplied through environment variables and must never be committed to the repository.

Required variables:

```bash
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT="linux:ava-trend-research:v1.0 (by /u/YOUR_REDDIT_USERNAME)"
```

Copy `.env.example` only as a local reference. The script itself reads environment variables directly.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Example

Search a small number of recent public posts:

```bash
export REDDIT_CLIENT_ID="..."
export REDDIT_CLIENT_SECRET="..."
export REDDIT_USER_AGENT="linux:ava-trend-research:v1.0 (by /u/YOUR_REDDIT_USERNAME)"

python3 reddit_client.py search \
  --query '"is there an app for"' \
  --limit 5
```

Read a few public comments from one public post:

```bash
python3 reddit_client.py comments \
  --post-id POST_ID \
  --limit 5
```

## Scope

This repository is intentionally small. It is the isolated Reddit API access layer that can be reviewed independently from the private local research workflow that consumes its read-only output.

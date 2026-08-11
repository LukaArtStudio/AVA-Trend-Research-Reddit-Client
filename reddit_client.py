#!/usr/bin/env python3
"""
AVA Trend Research — minimal read-only Reddit Data API client.

This module intentionally implements only:
  * OAuth application-token acquisition
  * GET /search
  * GET /comments/{post_id}

It does not implement any Reddit write action.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Any

import requests

TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
API_BASE = "https://oauth.reddit.com"
DEFAULT_TIMEOUT = 25


class ConfigError(RuntimeError):
    pass


class RedditAPIError(RuntimeError):
    pass


@dataclass(frozen=True)
class Config:
    client_id: str
    client_secret: str
    user_agent: str

    @classmethod
    def from_environment(cls) -> "Config":
        values = {
            "client_id": os.getenv("REDDIT_CLIENT_ID", "").strip(),
            "client_secret": os.getenv("REDDIT_CLIENT_SECRET", "").strip(),
            "user_agent": os.getenv("REDDIT_USER_AGENT", "").strip(),
        }
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise ConfigError(
                "Missing environment variable(s): "
                + ", ".join(name.upper() for name in missing)
            )
        if "YOUR_REDDIT_USERNAME" in values["user_agent"]:
            raise ConfigError("Replace YOUR_REDDIT_USERNAME in REDDIT_USER_AGENT.")
        return cls(**values)


class RedditReadOnlyClient:
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": config.user_agent})
        self._access_token = ""
        self._token_expires_at = 0.0

    def _ensure_token(self) -> None:
        if self._access_token and time.time() < self._token_expires_at - 60:
            return

        response = self.session.post(
            TOKEN_URL,
            auth=(self.config.client_id, self.config.client_secret),
            data={"grant_type": "client_credentials"},
            headers={"User-Agent": self.config.user_agent},
            timeout=DEFAULT_TIMEOUT,
        )
        self._raise_for_status(response, "OAuth token request")

        payload = response.json()
        token = str(payload.get("access_token", "")).strip()
        if not token:
            raise RedditAPIError("OAuth response did not contain an access token.")

        expires_in = int(payload.get("expires_in", 3600))
        self._access_token = token
        self._token_expires_at = time.time() + max(60, expires_in)

    def _get(self, path: str, *, params: dict[str, Any]) -> Any:
        self._ensure_token()
        headers = {
            "Authorization": f"bearer {self._access_token}",
            "User-Agent": self.config.user_agent,
        }
        response = self.session.get(
            API_BASE + path,
            params=params,
            headers=headers,
            timeout=DEFAULT_TIMEOUT,
        )
        self._raise_for_status(response, f"GET {path}")
        return response.json()

    @staticmethod
    def _raise_for_status(response: requests.Response, operation: str) -> None:
        if response.ok:
            return

        retry_after = response.headers.get("retry-after")
        rate_remaining = response.headers.get("x-ratelimit-remaining")
        detail = (
            f"{operation} failed: HTTP {response.status_code}. "
            f"rate_remaining={rate_remaining!r}, retry_after={retry_after!r}"
        )
        raise RedditAPIError(detail)

    def search_public_posts(
        self,
        query: str,
        *,
        limit: int = 5,
        time_filter: str = "month",
        sort: str = "new",
    ) -> list[dict[str, Any]]:
        """
        Search public posts and return a minimized representation.

        No author/profile field is retained.
        """
        limit = max(1, min(int(limit), 25))
        payload = self._get(
            "/search",
            params={
                "q": query,
                "sort": sort,
                "t": time_filter,
                "limit": limit,
                "raw_json": 1,
                "type": "link",
            },
        )

        results: list[dict[str, Any]] = []
        for child in payload.get("data", {}).get("children", []):
            data = child.get("data", {})
            post_id = str(data.get("id", "")).strip()
            permalink = str(data.get("permalink", "")).strip()
            results.append(
                {
                    "post_id": post_id,
                    "title": str(data.get("title", ""))[:500],
                    "text": str(data.get("selftext", ""))[:4000],
                    "subreddit": str(data.get("subreddit", ""))[:100],
                    "created_utc": data.get("created_utc"),
                    "permalink": (
                        f"https://www.reddit.com{permalink}" if permalink else ""
                    ),
                    "score": data.get("score"),
                    "num_comments": data.get("num_comments"),
                }
            )
        return results

    def read_public_comments(
        self,
        post_id: str,
        *,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Read a small number of public top-level comments for context.

        No author/profile field is retained.
        """
        post_id = post_id.strip()
        if not post_id:
            raise ValueError("post_id cannot be empty.")

        limit = max(1, min(int(limit), 10))
        payload = self._get(
            f"/comments/{post_id}",
            params={
                "limit": limit,
                "depth": 1,
                "sort": "top",
                "raw_json": 1,
            },
        )

        if not isinstance(payload, list) or len(payload) < 2:
            return []

        comments: list[dict[str, Any]] = []
        children = payload[1].get("data", {}).get("children", [])
        for child in children:
            if child.get("kind") != "t1":
                continue
            data = child.get("data", {})
            body = str(data.get("body", "")).strip()
            if not body:
                continue
            comments.append(
                {
                    "comment_id": str(data.get("id", "")),
                    "text": body[:3000],
                    "created_utc": data.get("created_utc"),
                    "score": data.get("score"),
                }
            )
            if len(comments) >= limit:
                break
        return comments


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Minimal read-only Reddit Data API client for AVA Trend Research."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    search = sub.add_parser("search", help="Search public Reddit posts.")
    search.add_argument("--query", required=True)
    search.add_argument("--limit", type=int, default=5)
    search.add_argument(
        "--time-filter",
        default="month",
        choices=["hour", "day", "week", "month", "year", "all"],
    )
    search.add_argument(
        "--sort",
        default="new",
        choices=["relevance", "hot", "top", "new", "comments"],
    )

    comments = sub.add_parser("comments", help="Read selected public comments.")
    comments.add_argument("--post-id", required=True)
    comments.add_argument("--limit", type=int, default=5)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        client = RedditReadOnlyClient(Config.from_environment())

        if args.command == "search":
            output = client.search_public_posts(
                args.query,
                limit=args.limit,
                time_filter=args.time_filter,
                sort=args.sort,
            )
        else:
            output = client.read_public_comments(
                args.post_id,
                limit=args.limit,
            )

        json.dump(output, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
        return 0

    except (ConfigError, RedditAPIError, ValueError, requests.RequestException) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

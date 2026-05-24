#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fetch GitHub repository information for HelloGitHub project submissions.

This script queries the GitHub API to retrieve metadata for submitted repositories,
including star count, description, language, and other relevant details.
"""

import os
import sys
import json
import time
import logging
from typing import Optional

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# GitHub API base URL
GITHUB_API_BASE = "https://api.github.com"

# Default request headers
HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# Request timeout in seconds — increased from 10 to 15 to reduce timeout errors
# on slow connections or when the API is under load
REQUEST_TIMEOUT = 15


def get_token() -> Optional[str]:
    """Retrieve GitHub personal access token from environment variables."""
    # Also check GH_TOKEN as an alternative env var name (used by GitHub CLI)
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        logger.warning(
            "GITHUB_TOKEN not set. API rate limits will be restricted to 60 req/hour."
        )
    return token


def build_headers() -> dict:
    """Build request headers, including authorization if token is available."""
    headers = HEADERS.copy()
    token = get_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_repo_info(owner: str, repo: str) -> Optional[dict]:
    """
    Fetch repository metadata from the GitHub API.

    Args:
        owner: The GitHub username or organization name.
        repo:  The repository name.

    Returns:
        A dictionary with repository details, or None on failure.
    """
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
    headers = build_headers()

    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        logger.error("HTTP error for %s/%s: %s", owner, repo, exc)
        return None
    except requests.exceptions.RequestException as exc:
        logger.error("Request failed for %s/%s: %s", owner, repo, exc)
        return None

    data = response.json()

    return {
        "full_name": data.get("full_name"),
        "description": data.get("description"),
        "html_url": data.get("html_url"),
        "homepage": data.get("homepage"),
        "language": data.get("language"),
        "stargazers_count": data.get("stargazers_count", 0),
        "forks_count": data.get("forks_count", 0),
        "open_issues_count": data.get("open_issues_count", 0),
        "topics": data.get("topics", []),
        "license": (data.get("license") or {}).get("spdx_id"),
        "archived": data.get("archived", False),
        "pushed_at": data.get("pushed_at"),
        "created_at": data.get("created_at"),
        # Include subscriber (watch) count — useful for gauging community interest

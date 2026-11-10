"""Collect GitHub numbers for the profile card and write cache/stats.json.

Lines of code come from the per-repo contributor statistics endpoint and are
cached in cache/loc.json by repo head commit (keyed by a hash of the repo name),
so a daily run only re-queries repos that actually moved. Private repos count
toward the totals when the token can see them, but no repo name is ever written
out: the card shows totals only and the cache keys are hashes.
"""

import hashlib
import json
import os
import pathlib
import time

import requests

USER = os.environ.get("GITHUB_USER", "Shawn5cents")
TOKEN = os.environ["GITHUB_TOKEN"]
ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "cache"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"}


def gql(query, **variables):
    for attempt in range(4):  # GitHub GraphQL occasionally returns an empty 502/504
        r = requests.post("https://api.github.com/graphql", headers=HEADERS,
                          json={"query": query, "variables": variables}, timeout=60)
        if r.status_code < 500 and r.text.strip():
            break
        time.sleep(5 * (attempt + 1))
    r.raise_for_status()
    body = r.json()
    if body.get("errors"):
        raise RuntimeError(body["errors"])
    return body["data"]


REPOS = """
query($login: String!, $after: String) {
  user(login: $login) {
    repositories(first: 100, after: $after, ownerAffiliations: OWNER) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        nameWithOwner isFork stargazerCount
        defaultBranchRef { target { oid } }
      }
    }
  }
}"""


def owned_repos():
    repos, after = [], None
    while True:
        page = gql(REPOS, login=USER, after=after)["user"]["repositories"]
        repos += page["nodes"]
        if not page["pageInfo"]["hasNextPage"]:
            return repos
        after = page["pageInfo"]["endCursor"]


def profile():
    q = """
    query($login: String!) {
      user(login: $login) {
        createdAt
        followers { totalCount }
        repositoriesContributedTo(contributionTypes: [COMMIT, PULL_REQUEST, REPOSITORY]) { totalCount }
      }
    }"""
    return gql(q, login=USER)["user"]


def repo_loc(name):
    """Return (additions, deletions, commits) authored by USER in one repo, or None if unavailable."""
    url = f"https://api.github.com/repos/{name}/stats/contributors"
    for _ in range(6):
        r = requests.get(url, headers=HEADERS, timeout=60)
        if r.status_code == 202:  # GitHub is computing the stats; ask again shortly
            time.sleep(5)
            continue
        if r.status_code in (204, 404, 409, 451):  # empty, hidden or blocked repo
            return 0, 0, 0
        r.raise_for_status()
        for c in r.json() or []:
            if (c.get("author") or {}).get("login", "").lower() == USER.lower():
                return (sum(w["a"] for w in c["weeks"]), sum(w["d"] for w in c["weeks"]), c["total"])
        return 0, 0, 0
    return None


def main():
    CACHE.mkdir(exist_ok=True)
    loc_path = CACHE / "loc.json"
    loc_cache = json.loads(loc_path.read_text()) if loc_path.exists() else {}

    repos = owned_repos()
    info = profile()
    adds = dels = commits = 0
    fresh = {}
    for repo in repos:
        if repo["isFork"]:
            continue
        name = repo["nameWithOwner"]
        # loc.json is committed to a public repo: key it by a hash so private repo names never leak
        key = hashlib.sha256(name.encode()).hexdigest()[:16]
        head = ((repo.get("defaultBranchRef") or {}).get("target") or {}).get("oid")
        cached = loc_cache.get(key)
        if cached and cached["head"] == head:
            a, d, k = cached["add"], cached["del"], cached.get("commits", 0)
        else:
            got = repo_loc(name)
            if got is None:  # still computing after retries: keep the old figure, refresh next run
                a, d, k = (cached["add"], cached["del"], cached.get("commits", 0)) if cached else (0, 0, 0)
                head = cached["head"] if cached else None
            else:
                a, d, k = got
        fresh[key] = {"head": head, "add": a, "del": d, "commits": k}
        adds += a
        dels += d
        commits += k

    stats = {
        "created_at": info["createdAt"],
        "repos": len(repos),
        "contributed": info["repositoriesContributedTo"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos if not r["isFork"]),
        "followers": info["followers"]["totalCount"],
        "commits": commits,
        "loc_add": adds,
        "loc_del": dels,
    }
    loc_path.write_text(json.dumps(fresh, indent=1, sort_keys=True) + "\n")
    (CACHE / "stats.json").write_text(json.dumps(stats, indent=1) + "\n")
    print(json.dumps(stats))


if __name__ == "__main__":
    main()

"""Rewrites the RECENT_REPOS block in README.md with my latest active repositories."""

import html
import json
import os
import re
import urllib.request

USER = os.environ.get("GH_USER", "MatheusAmorimm")
TOKEN = os.environ.get("GITHUB_TOKEN")
COUNT = 6
# repos that should never show up as a "project" card
SKIP = {USER.lower()}

README = "README.md"
START = "<!-- RECENT_REPOS:START -->"
END = "<!-- RECENT_REPOS:END -->"


def fetch_repos():
    url = f"https://api.github.com/users/{USER}/repos?sort=pushed&per_page=100"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        repos = json.load(resp)

    keep = [
        r for r in repos
        if not r["fork"] and not r["archived"] and r["name"].lower() not in SKIP
    ]
    return keep[:COUNT]


def card(repo):
    name = repo["name"]
    desc = html.escape(repo["description"] or "No description yet.")
    lang = repo["language"] or "Markdown"
    return (
        f'<td width="50%" align="center" valign="top">\n'
        f'<a href="https://github.com/{USER}/{name}">\n'
        f'<img width="100%" src="https://opengraph.githubassets.com/1/{USER}/{name}" alt="{name}" /><br />\n'
        f"<b>{name}</b>\n"
        f"</a><br />\n"
        f"<sub>{desc}</sub><br />\n"
        f"<sub><code>{lang}</code></sub>\n"
        f"</td>"
    )


def build_table(repos):
    rows = []
    for i in range(0, len(repos), 2):
        cells = "\n".join(card(r) for r in repos[i:i + 2])
        rows.append(f"<tr>\n{cells}\n</tr>")
    body = "\n".join(rows)
    return f'<div align="center">\n<table>\n{body}\n</table>\n</div>'


def main():
    repos = fetch_repos()
    if not repos:
        print("No repositories returned, keeping README as is.")
        return

    with open(README, encoding="utf-8") as f:
        content = f.read()

    block = f"{START}\n{build_table(repos)}\n{END}"
    new_content, subs = re.subn(
        re.escape(START) + r".*?" + re.escape(END), lambda _: block, content, flags=re.S
    )
    if subs == 0:
        raise SystemExit(f"Markers {START} / {END} not found in {README}")

    if new_content == content:
        print("README already up to date.")
        return

    with open(README, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"README updated with {len(repos)} repositories.")


if __name__ == "__main__":
    main()

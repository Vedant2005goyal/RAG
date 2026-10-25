import os
import json
import requests
from dotenv import load_dotenv

from schema import GithubIssues, GithubPR


load_dotenv()

owner = os.getenv("OWNER")
repo = os.getenv("REPO")


def fetch_closed_issue(owner: str, repo: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "doc-ingest-app",
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
    }

    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    results = []
    page = 1

    while True:
        params = {
            "page": page,
            "per_page": 100,
            "state": "closed",
        }

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=15,
        )

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            break

        data = response.json()

        if not data:
            break

        issue = [
            item for item in data
            if "pull_request" not in item
        ]

        results.extend(issue)
        page += 1

    return results


def fetch_closed_pr(owner: str, repo: str):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "doc-ingest-app",
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
    }

    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    results = []
    page = 1

    while True:
        params = {
            "page": page,
            "per_page": 100,
            "state": "closed",
        }

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=15,
        )

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            break

        data = response.json()

        if not data:
            break

        results.extend(data)
        page += 1

    return [
        pr for pr in results
        if pr.get("merged_at") is not None
    ]


def create_file(filename: str, function, *args):
    if os.path.exists(filename):
        print(f"Loading from {filename}")

        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)

    print("Fetching from Github")

    if args:
        data = function(*args)
    else:
        data = function(owner, repo)

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file)

    return data


def fetch_changed_file(number: int):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "doc-ingest-app",
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
    }

    url = (
        f"https://api.github.com/repos/{owner}/{repo}"
        f"/pulls/{number}/files"
    )

    response = requests.get(
        url,
        headers=headers,
        timeout=15,
    )

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return []

    return response.json()


def filter_prs_by_file(relevant_prs, payment_paths):
    result = []

    for pr in relevant_prs:
        files = fetch_changed_file(pr["number"])

        if any(
            file["filename"].startswith(payment_paths)
            for file in files
        ):
            result.append(pr)

    return result


def load_github_data():
    closed_issues = create_file(
        "closed_issues.json",
        fetch_closed_issue,
    )

    closed_prs = create_file(
        "closed_prs.json",
        fetch_closed_pr,
    )

    relevant_issues = []
    relevant_prs = []

    keywords = [
        "paymentservice",
        "payment service",
        "charge.js",
        "paymentfailure",
    ]

    payment_paths = (
        "src/payment/",
        "src/paymentservice/",
    )

    for issue in closed_issues:
        text = (
            (issue.get("title") or "")
            + " "
            + (issue.get("body") or "")
        ).lower()

        if any(keyword in text for keyword in keywords):
            relevant_issues.append(issue)

    for pr in closed_prs:
        text = (
            (pr.get("title") or "")
            + " "
            + (pr.get("body") or "")
        ).lower()

        if any(keyword in text for keyword in keywords):
            relevant_prs.append(pr)

    filtered_prs = create_file(
        "filtered_prs.json",
        filter_prs_by_file,
        relevant_prs,
        payment_paths,
    )

    issues = [
        GithubIssues.model_validate(data)
        for data in relevant_issues
    ]

    prs = [
        GithubPR.model_validate(data)
        for data in filtered_prs
    ]

    return issues, prs


if __name__ == "__main__":
    issues, prs = load_github_data()

    print(f"Loaded {len(issues)} relevant issues.")
    print(f"Loaded {len(prs)} relevant pull requests.")

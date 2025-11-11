from dotenv import load_dotenv
import os
load_dotenv()  # loads variables from .env
import time
import requests
import datetime

GITHUB_API_URL = "https://api.github.com/graphql"

# The main GraphQL query for fetching repositories and their star counts
REPO_QUERY = """
query ($cursor: String) {
  search(query: "stars:>0", type: REPOSITORY, first: 100, after: $cursor) {
    repositoryCount
    pageInfo {
      endCursor
      hasNextPage
    }
    nodes {
      ... on Repository {
        id
        name
        owner { login }
        nameWithOwner
        url
        stargazerCount
        updatedAt
      }
    }
  }
  rateLimit {
    cost
    remaining
    resetAt
  }
}
"""


class GitHubClient:
    """
    Handles interaction with GitHub's GraphQL API.
    Responsible for pagination, rate-limit handling, and retries.
    """

    def __init__(self, token=None, sleep_on_rate_limit=True):
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("Missing GITHUB_TOKEN environment variable or argument.")
        self.sleep_on_rate_limit = sleep_on_rate_limit

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def _run_query(self, query, variables=None, retries=5, backoff=2):
        """Execute the GraphQL query with retry logic."""
        for attempt in range(retries):
            try:
                response = self.session.post(
                    GITHUB_API_URL,
                    json={"query": query, "variables": variables or {}}
                )

                if response.status_code != 200:
                    raise Exception(f"GitHub API returned {response.status_code}: {response.text}")

                data = response.json()

                if "errors" in data:
                    # Retry only for transient issues like rate limit or 5xx errors
                    msg = str(data["errors"])
                    if "rate limit" in msg.lower() or "timeout" in msg.lower():
                        raise Exception(f"Temporary API error: {msg}")
                    else:
                        raise Exception(f"GraphQL error: {msg}")

                return data["data"]

            except Exception as e:
                wait = backoff * (2 ** attempt)
                print(f"[Retry {attempt + 1}/{retries}] Error: {e} — waiting {wait:.1f}s before retry")
                time.sleep(wait)

        raise Exception("Max retries reached — GitHub API unavailable.")

    def _handle_rate_limit(self, rate_limit):
        """Pause if remaining requests are low."""
        remaining = rate_limit["remaining"]
        reset_at = rate_limit["resetAt"]
        reset_time = datetime.datetime.strptime(reset_at, "%Y-%m-%dT%H:%M:%SZ")

        if remaining < 100 and self.sleep_on_rate_limit:
            wait_seconds = (reset_time - datetime.datetime.utcnow()).total_seconds()
            if wait_seconds > 0:
                print(f"⚠️ Rate limit almost reached. Sleeping for {int(wait_seconds)} seconds...")
                time.sleep(wait_seconds + 5)

    def fetch_repositories(self, limit=100000):
        """
        Fetch up to `limit` repositories from GitHub.
        Yields one repository dictionary per item.
        """
        cursor = None
        fetched = 0

        while fetched < limit:
            data = self._run_query(REPO_QUERY, {"cursor": cursor})

            search = data["search"]
            repos = search["nodes"]
            rate_limit = data["rateLimit"]

            # Handle rate limit
            self._handle_rate_limit(rate_limit)

            # Yield each repository
            for repo in repos:
                yield {
                "id": int(repo["id"].split("Repository")[-1], 16) if "Repository" in repo["id"] else hash(repo["id"]),
                "owner": repo["owner"],  # keep the dict
                "name": repo["name"],
                "full_name": repo["nameWithOwner"],
                "url": repo["url"],
                "current_stars": repo["stargazerCount"],
                "last_updated_at": repo["updatedAt"]
}


            fetched += len(repos)
            print(f"Fetched {fetched} repositories so far...")

            # Stop if there are no more pages
            if not search["pageInfo"]["hasNextPage"]:
                print("No more pages available.")
                break

            cursor = search["pageInfo"]["endCursor"]

        print(f"✅ Completed fetching {fetched} repositories.")


# --- For local testing only ---
if __name__ == "__main__":
    print("🔍 Testing GitHubClient with a small fetch (200 repos)...")

    # You can export your token before running:
    # setx GITHUB_TOKEN "your_personal_access_token_here"

    client = GitHubClient()
    count = 0
    for repo in client.fetch_repositories(limit=200):
        print(f"{repo['full_name']} ⭐ {repo['current_stars']}")
        count += 1

    print(f"Total repos fetched: {count}")


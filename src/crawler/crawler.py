import psycopg2
from datetime import date
from github_client import GitHubClient
from db import DB_CONFIG
import json


def upsert_repository(cur, repo):
    """Insert or update repository information."""
    # Handle owner being either string or dict
    owner = repo.get('owner')
    if isinstance(owner, dict):
        owner_login = owner.get('login')
    else:
        owner_login = owner  # already a string

    # Construct proper full_name using cleaned owner_login
    full_name = f"{owner_login}/{repo.get('name')}" if owner_login else repo.get('name')

    cur.execute("""
        INSERT INTO repositories (id, owner, name, full_name, url, current_stars)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE
        SET current_stars = EXCLUDED.current_stars,
            last_updated_at = NOW();
        """, (
            repo.get('id'),
            owner_login,      # ✅ use string value only
            repo.get('name'),
            full_name,        # ✅ correct full name
            repo.get('url'),
            repo.get('current_stars'),
        ))




def insert_star_snapshot(cur, repo_id, stars):
    """Insert a snapshot into stars_history (one per day per repo)."""
    cur.execute("""
        INSERT INTO stars_history (repo_id, snapshot_date, stars)
        VALUES (%s, %s, %s)
        ON CONFLICT (repo_id, snapshot_date) DO UPDATE
        SET stars = EXCLUDED.stars;
    """, (repo_id, date.today(), stars))

def crawl_and_store(limit=100000):
    """Fetch repositories and store in Postgres."""
    client = GitHubClient()
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    print(f"🚀 Starting crawl of {limit} repositories...")
    repos = client.fetch_repositories(limit=limit)

    count = 0
    for repo in repos:
        upsert_repository(cur, repo)
        insert_star_snapshot(cur, repo['id'], repo['current_stars'])
        count += 1
        if count % 500 == 0:
            conn.commit()
            print(f"✅ {count} repositories processed and committed.")

    conn.commit()
    cur.close()
    conn.close()
    print(f"🎉 Finished inserting {count} repositories into the database.")

if __name__ == "__main__":
    crawl_and_store()

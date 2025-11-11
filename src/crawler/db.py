import psycopg2

# Database connection configuration
DB_CONFIG = {
    "host": "localhost",
    "database": "GithubCrawler",
    "user": "postgres",
    "password": "root",
    "port": "5432"
}

def create_db_and_schema():
    """Connects to PostgreSQL and creates the necessary tables."""
    conn = None
    cur = None
    try:
        # Establish the connection
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # --- Create repositories table ---
        cur.execute("""
            CREATE TABLE IF NOT EXISTS repositories (
                id BIGINT PRIMARY KEY,
                owner TEXT NOT NULL,
                name TEXT NOT NULL,
                full_name TEXT UNIQUE,
                url TEXT,
                current_stars INTEGER,
                last_updated_at TIMESTAMPTZ DEFAULT NOW(),
                metadata JSONB
            );
        """)
        print("Table 'repositories' created.")

        # --- Create stars_history table ---
        cur.execute("""
            CREATE TABLE IF NOT EXISTS stars_history (
                id BIGSERIAL PRIMARY KEY,
                repo_id BIGINT REFERENCES repositories(id) ON DELETE CASCADE,
                snapshot_date DATE NOT NULL,
                stars INTEGER NOT NULL,
                UNIQUE (repo_id, snapshot_date)
            );
        """)
        print("Table 'stars_history' created.")

        # Commit the changes
        conn.commit()
        print("? All tables created successfully in database 'GithubCrawler'!")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f"Error: {error}")
    finally:
        # Close the cursor and connection
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    create_db_and_schema()

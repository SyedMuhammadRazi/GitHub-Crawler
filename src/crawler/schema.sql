-- repositories table
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

CREATE INDEX IF NOT EXISTS idx_repositories_owner_name ON repositories (owner, name);
CREATE INDEX IF NOT EXISTS idx_repositories_updated_at ON repositories (last_updated_at);

-- stars_history table
CREATE TABLE IF NOT EXISTS stars_history (
    id BIGSERIAL PRIMARY KEY,
    repo_id BIGINT REFERENCES repositories(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    stars INTEGER NOT NULL,
    UNIQUE (repo_id, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_stars_history_repo_date ON stars_history (repo_id, snapshot_date);

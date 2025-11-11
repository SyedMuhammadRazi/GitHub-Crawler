import os
import psycopg2
import pandas as pd

# Database connection from environment variables
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

# Read repositories table
df = pd.read_sql("SELECT * FROM repositories", conn)

# Save to CSV
df.to_csv("repositories.csv", index=False)
print("repositories.csv created successfully.")

conn.close()

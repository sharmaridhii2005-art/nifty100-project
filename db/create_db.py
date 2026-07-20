import os
import sqlite3

# Path of the database file
db_path = os.path.join("db", "nifty100.db")

# Connect to (or create) the database
conn = sqlite3.connect(db_path)

# Read the SQL schema file
with open("db/schema.sql", "r") as file:
    schema = file.read()

# Execute all SQL commands
conn.executescript(schema)

# Save changes
conn.commit()

# Close connection
conn.close()

print("Database created successfully: db/nifty100.db")
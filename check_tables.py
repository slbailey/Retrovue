import sqlite3

conn = sqlite3.connect("retrovue.db")
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print("Tables created:", tables)
conn.close()

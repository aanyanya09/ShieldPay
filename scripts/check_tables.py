import glob
import sqlite3

files = glob.glob("*.db")
print("Database files found:", files)
if not files:
    raise SystemExit("No .db file in this folder. Run the server once, then try again.")

conn = sqlite3.connect(files[0])
rows = conn.execute(
    "select name, sql from sqlite_master where type='table' order by name"
).fetchall()
for name, sql in rows:
    print("\n==", name)
    print(sql)

import sqlite3

conn = sqlite3.connect("bank.db")
print("表：", conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
for col in conn.execute("PRAGMA table_info(users)"):
    print(col)
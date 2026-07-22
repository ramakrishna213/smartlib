import sqlite3

conn = sqlite3.connect("instance/smartlib.db")
cursor = conn.cursor()

cursor.execute("ALTER TABLE books ADD COLUMN pdf_file VARCHAR(255)")

conn.commit()
conn.close()

print("pdf_file column added successfully")
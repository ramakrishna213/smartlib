import sqlite3

conn = sqlite3.connect("instance/smartlib.db")   # Change path if needed
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE books ADD COLUMN pdf_file TEXT")
    conn.commit()
    print("✅ pdf_file column added successfully.")
except Exception as e:
    print("Error:", e)

conn.close()

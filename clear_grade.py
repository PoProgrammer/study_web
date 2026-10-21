import sqlite3
import os

DB_FILE = os.path.join("data", "study.db")

# آیدی عددی تلگرام خودت رو اینجا بذار
MY_TELEGRAM_ID = 8649348758 

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# پاک کردن پایه و رشته
cursor.execute("""
    UPDATE users 
    SET grade = NULL, field = NULL 
    WHERE telegram_id = ?
""", (MY_TELEGRAM_ID,))

conn.commit()

# چک کردن نتیجه
cursor.execute("SELECT first_name, grade, field FROM users WHERE telegram_id = ?", (MY_TELEGRAM_ID,))
user = cursor.fetchone()

if user:
    print(f"✅ اطلاعات کاربر {user[0]} برای تست ریست شد.")
    print(f"🎓 پایه فعلی: {user[1]}")
    print(f"📚 رشته فعلی: {user[2]}")
else:
    print("❌ کاربر پیدا نشد.")

conn.close()
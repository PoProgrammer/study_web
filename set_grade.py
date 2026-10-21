import sqlite3
import os

# مسیر دیتابیس
DB_FILE = os.path.join("data", "study.db")

# اتصال به دیتابیس
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# آیدی عددی خودت رو اینجا بذار
MY_TELEGRAM_ID = 8649348758

# آپدیت کردن پایه و رشته
cursor.execute("""
    UPDATE users 
    SET grade = 'دوازدهم', field = 'تجربی' 
    WHERE telegram_id = ?
""", (MY_TELEGRAM_ID,))

conn.commit()

# چک کردن اینکه تغییر اعمال شده یا نه
cursor.execute("SELECT first_name, grade, field FROM users WHERE telegram_id = ?", (MY_TELEGRAM_ID,))
user = cursor.fetchone()

if user:
    print(f"✅ اطلاعات با موفقیت آپدیت شد:")
    print(f"👤 اسم: {user[0]}")
    print(f"🎓 پایه: {user[1]}")
    print(f"📚 رشته: {user[2]}")
else:
    print("❌ کاربر پیدا نشد. آیدی رو چک کن.")

conn.close()
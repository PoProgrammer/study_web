import os
if os.path.exists("data/study.db"):
    os.remove("data/study.db")
    print("✅ دیتابیس پاک شد.")
else:
    print("⚠️ دیتابیسی وجود نداشت.")
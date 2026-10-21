import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from database_api import router as database_router
from bot_2 import init_db

app = FastAPI(title="StudyBot WebApp API")

@app.on_event("startup")
def startup():
    init_db()

# سرو کردن فایل‌های استاتیک
app.mount("/static", StaticFiles(directory="."), name="static")

# سرو کردن پوشه آپلودها
os.makedirs("uploads/receipts", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# اتصال APIها
app.include_router(database_router, prefix="/api")

# ==========================================
# مسیرهای صفحات (بدون .html)
# ==========================================
@app.get("/")
def read_root():
    return FileResponse("dashboard.html")

@app.get("/dashboard")
def read_dashboard():
    return FileResponse("dashboard.html")

@app.get("/setup")
def read_setup():
    return FileResponse("setup.html")

@app.get("/subjects")
def read_subjects():
    return FileResponse("subjects.html")

@app.get("/study")
def read_study():
    return FileResponse("study.html")

@app.get("/exam")
def read_exam():
    return FileResponse("exam.html")

@app.get("/mock-exam")
def read_mock_exam():
    return FileResponse("mock_exam.html")

@app.get("/league")
def read_league():
    return FileResponse("league.html")

@app.get("/report")
def read_report():
    return FileResponse("report.html")

@app.get("/support")
def read_support():
    return FileResponse("support.html")

@app.get("/admin-support")
def read_admin_support():
    return FileResponse("admin_support.html")

@app.get("/coins")
def read_coins():
    return FileResponse("coins.html")

@app.get("/stats")
def read_stats():
    return FileResponse("stats.html")

@app.get("/achievements")
def read_achievements():
    return FileResponse("achievements.html")

@app.get("/plan")
def read_plan():
    return FileResponse("plan.html")

@app.get("/quests")
def read_quests():
    return FileResponse("quests.html")

@app.get("/qbank")
def read_qbank():
    return FileResponse("qbank.html")

@app.get("/konkur")
def read_konkur():
    return FileResponse("konkur.html")

@app.get("/ai")
def read_ai():
    return FileResponse("ai.html")

@app.get("/summary")
def read_summary():
    return FileResponse("summary.html")

@app.get("/stars")
def read_stars():
    return FileResponse("stars.html")

@app.get("/referral")
def read_referral():
    return FileResponse("referral.html")

@app.get("/subscription")
def read_subscription():
    return FileResponse("subscription.html")

@app.get("/admin-payments")
def read_admin_payments():
    return FileResponse("admin_payments.html")

@app.get("/groups")
def read_groups():
    return FileResponse("groups.html")

@app.get("/battle")
def read_battle():
    return FileResponse("battle.html")
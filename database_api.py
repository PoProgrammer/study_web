from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from datetime import datetime, timedelta
import json
import os
import shutil
import random
import string
import hashlib
import jdatetime

from bot_2 import (
    get_user, get_user_by_id, save_user, get_subjects, add_subject, 
    set_user_grade, set_user_field,
    start_session, get_subject, get_db,
    save_exam, complete_exam, check_exam_exists,
    save_mock_exam, complete_mock_exam, get_mock_exam,
    add_coins, add_league_points, check_and_grant_achievements,
    get_league_leaderboard, get_user_league_points, get_user_league_rank,
    get_league_participants_count, get_user_exams_count,
    add_support_message, get_support_thread, get_support_thread_recent,
    get_all_support_users, mark_support_read, mark_admin_messages_read,
    get_support_unread_count_for_user,
    get_user_stats, get_detailed_stats,
    get_achievements_text, get_user_achievements,
    save_plan, get_latest_plan, delete_plans,
    ensure_daily_quests, get_daily_quests, check_quest_completion,
    claim_quest_reward, get_daily_quests_text,
    get_question_bank, get_question_bank_stats, clear_question_bank,
    remove_from_question_bank, add_to_question_bank,
    get_mock_exam_history,
    save_summary, get_summaries, get_summary, delete_summary,
    get_user_stars, get_claimed_star_rewards, get_next_star_milestone,
    register_daily_star, check_and_claim_star_rewards,
    get_jalali_month_display, get_days_until_month_end,
    generate_referral_code, get_user_referral_stats, get_total_referral_discount,
    calculate_purchase, get_plan_price_toman, get_plan_days,
    create_payment_request, get_payment_request,
    get_pending_payments, get_all_payments, get_user_payments,
    approve_payment, reject_payment,
    get_unseen_payment_count, mark_payments_seen,
    create_group, get_group, get_group_by_code, get_user_group,
    join_group, leave_group, get_group_members, get_group_owner_id,
    is_group_owner, create_group_challenge, get_group_challenge,
    cancel_group_challenge, get_challenge_progress,
    create_battle, get_battle_by_code, get_battle, join_battle,
    save_battle_answer, complete_battle, get_user_battle_history,
    get_ai_chat_history, save_ai_chat_message, clear_ai_chat_history,
    get_user_plans, save_user_plan, delete_user_plan
)
from bot_3 import (
    generate_konkur_questions, generate_exam_questions, 
    generate_report_chart_url, generate_weekly_plan, ask_advisor,
    calculate_konkur_rank, format_konkur_prediction,
    generate_summary, PLAN_NAMES, DURATION_NAMES,
    generate_battle_questions, generate_battle_code,
)
from bot_1 import (
    KONKUR_EXAM_STRUCTURE, LEAGUE_POINTS, COINS_MOCK_EXAM, 
    ADMIN_ID, COIN_TO_TOMAN, COIN_DISCOUNT_PERCENT, STAR_REWARDS,
    GROUP_MAX_MEMBERS, GROUP_CHALLENGE_TYPES, GROUP_CHALLENGE_DURATIONS,
    BATTLE_WAGER, BATTLE_QUESTIONS, COINS_BATTLE_WIN,
)

router = APIRouter()

# ============================================================
# مدل‌ها
# ============================================================
class SubjectCreate(BaseModel):
    book: str
    grade: str
    field: str = ""

class UserSetup(BaseModel):
    grade: str
    field: str

class StudySessionCreate(BaseModel):
    subject_id: int
    chapter: str
    duration: int

class ExamStart(BaseModel):
    subject_id: int
    chapter: str
    count: int = 10

class SupportMessage(BaseModel):
    message: str

class PlanRequest(BaseModel):
    goal: str
    subjects: str
    hours: float
    off_days: str

class QuestClaim(BaseModel):
    quest_id: str

class AdvisorQuestion(BaseModel):
    question: str

class SummaryRequest(BaseModel):
    title: str
    subject: str
    text: str

class PaymentStart(BaseModel):
    plan_key: str
    duration_key: str

class PaymentAction(BaseModel):
    admin_id: int
    note: str = ""

class PaymentReceiptSubmit(BaseModel):
    sender_card: str
    tracking_code: str

class GroupCreate(BaseModel):
    name: str

class GroupJoin(BaseModel):
    code: str

class ChallengeCreate(BaseModel):
    challenge_type: str
    goal_value: int
    duration_type: str

class BattleCreate(BaseModel):
    subject_id: int

class BattleJoin(BaseModel):
    code: str

class BattleAnswers(BaseModel):
    answers: list[int]

class AuthRegister(BaseModel):
    first_name: str
    phone: str
    password: str

class AuthLogin(BaseModel):
    phone: str
    password: str

# ============================================================
# احراز هویت
# ============================================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

@router.post("/auth/register")
def register_user_auth(req: AuthRegister):
    phone = req.phone.strip()
    if phone.startswith("0"):
        phone = phone[1:]
        
    if len(phone) != 10:
        raise HTTPException(status_code=400, detail="شماره موبایل نامعتبر است")
        
    user = get_user(phone)
    if user:
        raise HTTPException(status_code=400, detail="این شماره موبایل قبلاً ثبت‌نام کرده است")
        
    pwd_hash = hash_password(req.password)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (telegram_id, first_name, username, coins, streak, joined_at, plan, password_hash)
        VALUES (?, ?, ?, 0, 0, ?, 'free', ?)
    """, (phone, req.first_name, "", datetime.now().isoformat(), pwd_hash))
    conn.commit()
    conn.close()
    
    return {"status": "success", "message": "ثبت‌نام با موفقیت انجام شد", "phone": phone}

@router.post("/auth/login")
def login_user(req: AuthLogin):
    phone = req.phone.strip()
    if phone.startswith("0"):
        phone = phone[1:]
        
    user = get_user(phone)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر با این شماره پیدا نشد")
        
    if not user["password_hash"]:
        raise HTTPException(status_code=400, detail="برای این حساب رمز عبور تنظیم نشده است")
        
    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="رمز عبور اشتباه است")
        
    return {
        "status": "success",
        "user": {
            "telegram_id": user["telegram_id"],
            "first_name": user["first_name"],
            "grade": user["grade"],
            "field": user["field"],
            "coins": user["coins"],
            "avatar": user["avatar"] if "avatar" in user.keys() else "🦊"
        }
    }

# ============================================================
# کاربر
# ============================================================
@router.get("/user/{telegram_id}")
def get_user_profile(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
    return {
        "telegram_id": user["telegram_id"],
        "first_name": user["first_name"],
        "coins": user["coins"],
        "grade": user["grade"],
        "field": user["field"],
        "plan": user["plan"],
        "avatar": user["avatar"] if "avatar" in user.keys() else "🦊"
    }

@router.post("/user/setup/{telegram_id}")
def setup_user_profile(telegram_id: int, setup: UserSetup):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
    set_user_grade(user["id"], setup.grade)
    set_user_field(user["id"], setup.field)
    return {"status": "success", "message": "پایه و رشته ثبت شد"}

# ============================================================
# درس‌ها
# ============================================================
@router.get("/subjects/{telegram_id}")
def get_user_subjects(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
    subjects = get_subjects(user["id"])
    result = []
    for s in subjects:
        result.append({"id": s["id"], "book": s["book"], "grade": s["grade"], "field": s["field"]})
    return result

@router.post("/subjects/{telegram_id}")
def add_new_subject(telegram_id: int, subject: SubjectCreate):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
    subject_id = add_subject(user["id"], subject.grade, subject.field, subject.book)
    return {"status": "success", "subject_id": subject_id, "message": "درس اضافه شد"}

# ============================================================
# مطالعه
# ============================================================
@router.post("/study/start/{telegram_id}")
def start_study_session(telegram_id: int, session: StudySessionCreate):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
    subject = get_subject(session.subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="درس پیدا نشد")
    session_id = start_session(user["id"], session.subject_id, session.chapter, "", session.duration)
    return {"status": "success", "session_id": session_id}

@router.post("/study/finish/{session_id}")
def finish_study_session(session_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE sessions SET end_time = ?, status = 'completed' WHERE id = ?", (datetime.now().isoformat(), session_id))
    conn.commit()
    cursor.execute("SELECT user_id, duration FROM sessions WHERE id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        points = row['duration'] * LEAGUE_POINTS["minute_study"]
        add_league_points(row['user_id'], points)
        return {"status": "success", "points": points}
    return {"status": "error"}

# ============================================================
# امتحان
# ============================================================
@router.post("/exam/start/{telegram_id}")
def start_exam(telegram_id: int, exam_data: ExamStart):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
    subject = get_subject(exam_data.subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="درس پیدا نشد")
    if check_exam_exists(user["id"], exam_data.subject_id, exam_data.chapter):
        raise HTTPException(status_code=400, detail="شما قبلاً از این فصل امتحان داده‌اید.")
    questions = generate_exam_questions(subject["grade"], subject["field"], subject["book"], exam_data.chapter, "کل فصل", exam_data.count)
    if not questions:
        raise HTTPException(status_code=500, detail="خطا در ساخت سوالات.")
    correct_answers = [q['answer'] for q in questions]
    exam_id = save_exam(user["id"], exam_data.subject_id, exam_data.chapter, questions, correct_answers)
    return {"exam_id": exam_id, "questions": questions}

@router.post("/exam/finish/{exam_id}")
def finish_exam(exam_id: int, user_answers: list[int], telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT correct_answers, questions, subject_id, chapter FROM exams WHERE id = ?", (exam_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="آزمون پیدا نشد")
    correct_answers = json.loads(row['correct_answers'])
    questions = json.loads(row['questions'])
    subject_id = row['subject_id']
    chapter = row['chapter']
    
    subject = get_subject(subject_id)
    
    score = 0
    total = len(correct_answers)
    wrong_count = 0
    for i, ca in enumerate(correct_answers):
        ua = user_answers[i] if i < len(user_answers) else -1
        if ua == ca:
            score += 1
        else:
            wrong_count += 1
            if subject:
                add_to_question_bank(
                    user["id"], subject_id, chapter, subject["grade"], subject["field"], subject["book"],
                    questions[i]['q'], questions[i]['options'], ca, ua
                )
            
    percent = (score / total) * 100 if total > 0 else 0
    if percent < 50:
        coins, status = 0, "❌ ضعیف"
    elif percent < 70:
        coins, status = 0, "✅ خوب"
    elif percent < 90:
        coins, status = 0, "🎉 عالی"
    else:
        coins, status = COINS_MOCK_EXAM, "🏆 فوق‌العاده"
    complete_exam(exam_id, user_answers, score, coins)
    if coins:
        add_coins(user["id"], coins)
    league_pts = 0
    if percent >= 90:
        league_pts = LEAGUE_POINTS["exam_90"]
    elif percent >= 70:
        league_pts = LEAGUE_POINTS["exam_70"]
    if league_pts:
        add_league_points(user["id"], league_pts)
    new_ach = check_and_grant_achievements(user["id"])
    return {
        "score": score, "total": total, "wrong": wrong_count,
        "percent": percent, "status": status, "coins": coins,
        "league_points": league_pts,
        "new_achievements": [a['name'] for a in new_ach]
    }

# ============================================================
# آزمون کنکور
# ============================================================
@router.post("/mock_exam/start/{telegram_id}")
def start_mock_exam(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
    field = user["field"]
    if not field or field not in KONKUR_EXAM_STRUCTURE:
        raise HTTPException(status_code=400, detail="رشته شما تعریف نشده است.")
    structure = KONKUR_EXAM_STRUCTURE[field]
    questions = generate_konkur_questions(field, structure["subjects"])
    if not questions:
        raise HTTPException(status_code=500, detail="خطا در ساخت سوالات.")
    correct_answers = [q['answer'] for q in questions]
    books_json = [{"book": s['name'], "count": s['count']} for s in structure["subjects"]]
    mock_id = save_mock_exam(user["id"], f"konkur_{field}", len(questions), structure["duration_minutes"], books_json, questions, correct_answers)
    return {"mock_id": mock_id, "duration_minutes": structure["duration_minutes"], "questions": questions}

@router.post("/mock_exam/finish/{mock_id}")
def finish_mock_exam(mock_id: int, user_answers: list[int], telegram_id: int):
    mock = get_mock_exam(mock_id)
    if not mock:
        raise HTTPException(status_code=404, detail="آزمون پیدا نشد")
    correct_answers = json.loads(mock['correct_answers'])
    questions = json.loads(mock['questions'])
    total_correct = 0
    total_wrong = 0
    total_blank = 0
    results_by_book = {}
    for i, q in enumerate(questions):
        book = q.get('subject', 'نامشخص')
        if book not in results_by_book:
            results_by_book[book] = {"correct": 0, "wrong": 0, "blank": 0, "total": 0}
        results_by_book[book]["total"] += 1
        ua = user_answers[i] if i < len(user_answers) else -1
        ca = correct_answers[i]
        if ua == -1:
            results_by_book[book]["blank"] += 1
            total_blank += 1
        elif ua == ca:
            results_by_book[book]["correct"] += 1
            total_correct += 1
        else:
            results_by_book[book]["wrong"] += 1
            total_wrong += 1
    total = len(questions)
    percent = (total_correct / total) * 100 if total > 0 else 0
    if percent < 30:
        coins, status = 0, "❌ ضعیف"
    elif percent < 50:
        coins, status = 0, "⚠️ قابل قبول"
    elif percent < 70:
        coins, status = 0, "✅ خوب"
    elif percent < 90:
        coins, status = COINS_MOCK_EXAM // 2, "🎉 عالی"
    else:
        coins, status = COINS_MOCK_EXAM, "🏆 فوق‌العاده"
    if coins:
        add_coins(mock['user_id'], coins)
    league_pts = LEAGUE_POINTS["mock_exam"]
    add_league_points(mock['user_id'], league_pts)
    complete_mock_exam(mock_id, user_answers, results_by_book, total_correct, total_wrong, total_blank, percent, coins)
    new_ach = check_and_grant_achievements(mock['user_id'])
    return {
        "total_correct": total_correct, "total_wrong": total_wrong, "total_blank": total_blank,
        "percent": percent, "status": status, "coins_earned": coins,
        "league_points": league_pts, "results_by_book": results_by_book,
        "new_achievements": [a['name'] for a in new_ach]
    }

# ============================================================
# لیگ
# ============================================================
@router.get("/league/leaderboard/{telegram_id}")
def get_league_data(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
    grade = user["grade"]
    if not grade:
        raise HTTPException(status_code=400, detail="پایه شما تعیین نشده است.")
    leaderboard = get_league_leaderboard(grade, limit=20)
    user_points = get_user_league_points(user["id"])
    user_rank = get_user_league_rank(user["id"])
    participants = get_league_participants_count(grade)
    return {
        "grade": grade,
        "user_points": user_points,
        "user_rank": user_rank,
        "participants": participants,
        "leaderboard": [{"name": row["first_name"], "points": row["points"], "is_me": row["user_id"] == user["id"]} for row in leaderboard]
    }

# ============================================================
# کارنامه
# ============================================================
@router.get("/report/{telegram_id}")
def get_user_report(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT e.id, e.chapter, e.score, e.completed_at, s.book, s.grade, s.field
        FROM exams e JOIN subjects s ON e.subject_id = s.id
        WHERE e.user_id = ? AND e.status = 'completed'
        ORDER BY e.completed_at ASC
    """, (user["id"],))
    exams = cursor.fetchall()
    
    cursor.execute("""
        SELECT id, percent, total_questions, completed_at FROM mock_exams
        WHERE user_id = ? AND status = 'completed' ORDER BY completed_at ASC
    """, (user["id"],))
    mocks = cursor.fetchall()
    
    conn.close()

    if not exams and not mocks:
        return {"has_data": False}

    chapter_stats = {}
    for e in exams:
        if e['score'] is None:
            continue
        percent = e['score'] * 10
        key = f"{e['book']} — {e['chapter']}"
        if key not in chapter_stats:
            chapter_stats[key] = []
        chapter_stats[key].append(percent)
        
    strengths = []
    weaknesses = []
    
    for key, scores in chapter_stats.items():
        avg = sum(scores) / len(scores)
        if avg >= 70:
            strengths.append({"label": key, "avg": round(avg, 1)})
        elif avg < 50:
            weaknesses.append({"label": key, "avg": round(avg, 1)})

    labels = ["هفته ۱", "هفته ۲", "هفته ۳", "هفته ۴"]
    values = [0, 0, 0, 0]
    now = datetime.now()
    
    for e in exams:
        try:
            dt = datetime.fromisoformat(e['completed_at'])
            days_ago = (now - dt).days
            if 0 <= days_ago < 7: values[3] += e['score'] * 10
            elif 7 <= days_ago < 14: values[2] += e['score'] * 10
            elif 14 <= days_ago < 21: values[1] += e['score'] * 10
            elif 21 <= days_ago < 28: values[0] += e['score'] * 10
        except: pass

    for m in mocks:
        try:
            dt = datetime.fromisoformat(m['completed_at'])
            days_ago = (now - dt).days
            if 0 <= days_ago < 7: values[3] += m['percent']
            elif 7 <= days_ago < 14: values[2] += m['percent']
            elif 14 <= days_ago < 21: values[1] += m['percent']
            elif 21 <= days_ago < 28: values[0] += m['percent']
        except: pass

    for i in range(4):
        count = 0
        for e in exams:
            try:
                dt = datetime.fromisoformat(e['completed_at'])
                if (3-i)*7 <= (now - dt).days < (4-i)*7: count += 1
            except: pass
        for m in mocks:
            try:
                dt = datetime.fromisoformat(m['completed_at'])
                if (3-i)*7 <= (now - dt).days < (4-i)*7: count += 1
            except: pass
        if count > 0:
            values[i] = values[i] / count

    chart_url = generate_report_chart_url(labels, values)
    
    all_scores = [e['score'] * 10 for e in exams] + [m['percent'] for m in mocks]
    total_count = len(all_scores)
    avg = sum(all_scores) / total_count if total_count > 0 else 0
    
    return {
        "has_data": True,
        "total_count": total_count,
        "avg": round(avg, 1),
        "best": {"label": "بهترین", "percent": round(max(all_scores), 1) if all_scores else 0},
        "worst": {"label": "ضعیف‌ترین", "percent": round(min(all_scores), 1) if all_scores else 0},
        "strengths": strengths[:5],
        "weaknesses": weaknesses[:5],
        "chart_url": chart_url
    }

# ============================================================
# پشتیبانی
# ============================================================
@router.get("/support/{telegram_id}")
def get_user_support_messages(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
    
    messages = get_support_thread_recent(user["id"], limit=30)
    mark_admin_messages_read(user["id"])
    
    result = []
    for m in messages:
        result.append({
            "sender": m["sender"],
            "text": m["message_text"],
            "date": m["created_at"]
        })
    return {"messages": result}

@router.post("/support/{telegram_id}")
def send_support_message(telegram_id: int, msg: SupportMessage):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
    
    add_support_message(user["id"], "user", msg.message)
    return {"status": "success"}

@router.get("/admin/support/users")
def get_admin_support_users(admin_id: int):
    if admin_id != ADMIN_ID:
        raise HTTPException(status_code=403, detail="شما ادمین نیستید")
        
    users = get_all_support_users()
    result = []
    for u in users:
        result.append({
            "user_id": u["id"],
            "name": u["first_name"],
            "unread": u["unread_count"] or 0,
            "last_message": u["last_message_at"]
        })
    return {"users": result}

@router.get("/admin/support/thread/{target_user_id}")
def get_admin_support_thread(target_user_id: int, admin_id: int):
    if admin_id != ADMIN_ID:
        raise HTTPException(status_code=403, detail="شما ادمین نیستید")
        
    messages = get_support_thread_recent(target_user_id, limit=50)
    mark_support_read(target_user_id)
    
    result = []
    for m in messages:
        result.append({
            "sender": m["sender"],
            "text": m["message_text"],
            "date": m["created_at"]
        })
    return {"messages": result}

@router.post("/admin/support/reply/{target_user_id}")
def admin_reply_support(target_user_id: int, admin_id: int, msg: SupportMessage):
    if admin_id != ADMIN_ID:
        raise HTTPException(status_code=403, detail="شما ادمین نیستید")
        
    add_support_message(target_user_id, "admin", msg.message)
    return {"status": "success"}

# ============================================================
# سکه
# ============================================================
@router.get("/coins/{telegram_id}")
def get_coins_info(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
    
    return {
        "coins": user["coins"],
        "coin_to_toman": COIN_TO_TOMAN,
        "coin_discount_percent": COIN_DISCOUNT_PERCENT
    }

# ============================================================
# آمار
# ============================================================
@router.get("/stats/{telegram_id}")
def get_stats(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    stats = get_user_stats(user["id"])
    
    return {
        "today": round(stats["today"] / 60, 1),
        "week": round(stats["week"] / 60, 1),
        "all": round(stats["all"] / 60, 1),
        "sessions": stats["count"],
        "exams": stats["exams"]
    }

# ============================================================
# دستاوردها
# ============================================================
@router.get("/achievements/{telegram_id}")
def get_achievements(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    text = get_achievements_text(user["id"])
    
    return {"text": text}

# ============================================================
# برنامه‌ریزی
# ============================================================
@router.get("/plan/{telegram_id}")
def get_plan(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    plan = get_latest_plan(user["id"])
    if not plan:
        return {"has_plan": False}
        
    return {
        "has_plan": True,
        "goal": plan["goal"],
        "subjects": plan["subjects"],
        "hours": plan["hours_per_day"],
        "off_days": plan["off_days"],
        "text": plan["plan_text"]
    }

@router.post("/plan/{telegram_id}")
def create_plan(telegram_id: int, req: PlanRequest):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    plan_text = generate_weekly_plan(req.goal, req.subjects, req.hours, req.off_days)
    if not plan_text:
        raise HTTPException(status_code=500, detail="خطا در ساخت برنامه")
        
    save_plan(user["id"], req.goal, req.subjects, req.hours, req.off_days, plan_text)
    save_user_plan(user["id"], req.goal, req.subjects, req.hours, req.off_days, plan_text)
    
    return {"status": "success", "plan_text": plan_text}

@router.delete("/plan/{telegram_id}")
def delete_user_plan(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    delete_plans(user["id"])
    return {"status": "success"}

@router.get("/plan/history/{telegram_id}")
def get_plan_history(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
    
    plans = get_user_plans(user["id"])
    result = []
    for p in plans:
        result.append({
            "id": p["id"],
            "goal": p["goal"],
            "subjects": p["subjects"],
            "hours": p["hours"],
            "off_days": p["off_days"] or "",
            "text": p["plan_text"],
            "date": p["created_at"][:10]
        })
    return {"plans": result}

# ============================================================
# مأموریت‌ها
# ============================================================
@router.get("/quests/{telegram_id}")
def get_quests(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    ensure_daily_quests(user["id"])
    check_quest_completion(user["id"])
    
    quests = get_daily_quests(user["id"])
    
    result = []
    for q in quests:
        result.append({
            "id": q["id"],
            "text": q["text"],
            "coins": q["coins"],
            "completed": bool(q["completed"]),
            "claimed": bool(q["claimed"])
        })
        
    return {"quests": result}

@router.post("/quests/{telegram_id}/claim")
def claim_quest(telegram_id: int, req: QuestClaim):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    result = claim_quest_reward(user["id"], req.quest_id)
    if not result:
        raise HTTPException(status_code=400, detail="امکان دریافت این جایزه وجود ندارد.")
        
    return {"status": "success", "coins": result["coins"]}

# ============================================================
# بانک سوالات
# ============================================================
@router.get("/qbank/{telegram_id}")
def get_user_qbank(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    stats = get_question_bank_stats(user["id"])
    return {
        "total": stats["total"],
        "by_chapter": [{"book": r["book"], "chapter": r["chapter"], "count": r["c"]} for r in stats["by_chapter"]]
    }

@router.get("/qbank/{telegram_id}/questions")
def get_qbank_questions(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    questions = get_question_bank(user["id"], limit=10)
    result = []
    for q in questions:
        result.append({
            "id": q["id"],
            "text": q["question_text"],
            "options": json.loads(q["options"]),
            "correct": q["correct_answer"],
            "user_answer": q["user_answer"]
        })
    return {"questions": result}

@router.delete("/qbank/{telegram_id}")
def clear_qbank(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    clear_question_bank(user["id"])
    return {"status": "success"}

# ============================================================
# پیش‌بینی رتبه
# ============================================================
@router.get("/konkur/{telegram_id}")
def get_konkur_prediction(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
    
    if not user["field"]:
        raise HTTPException(status_code=400, detail="رشته شما تعریف نشده است.")
        
    mocks = get_mock_exam_history(user["id"], limit=1)
    if not mocks:
        return {"has_data": False}
        
    result = calculate_konkur_rank(user["id"], user["field"])
    if not result:
        return {"has_data": False}
        
    return {
        "has_data": True,
        "rank": result["rank"],
        "percent": result["percent"],
        "majors": result["majors"]
    }

# ============================================================
# مشاور هوشمند
# ============================================================
@router.post("/advisor/{telegram_id}")
def ask_ai_advisor(telegram_id: int, req: AdvisorQuestion):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    save_ai_chat_message(user["id"], "user", req.question)
        
    response = ask_advisor(user, req.question)
    if not response:
        raise HTTPException(status_code=500, detail="خطا در ارتباط با هوش مصنوعی.")
    
    save_ai_chat_message(user["id"], "ai", response)
        
    return {"answer": response}

@router.get("/ai/chat-history/{telegram_id}")
def get_ai_chat_history_api(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
    
    messages = get_ai_chat_history(user["id"])
    return {"messages": messages}

@router.delete("/ai/chat-history/{telegram_id}")
def clear_ai_chat_history_api(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
    
    clear_ai_chat_history(user["id"])
    return {"status": "success"}

# ============================================================
# خلاصه‌ساز
# ============================================================
@router.post("/summary/{telegram_id}")
def create_summary(telegram_id: int, req: SummaryRequest):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    if len(req.text) < 50:
        raise HTTPException(status_code=400, detail="متن خیلی کوتاه است.")
        
    summary_text = generate_summary(req.text, req.title, req.subject)
    if not summary_text:
        raise HTTPException(status_code=500, detail="خطا در ساخت خلاصه با هوش مصنوعی.")
        
    summary_id = save_summary(user["id"], req.title, req.subject, summary_text)
    
    return {"status": "success", "summary_id": summary_id, "summary_text": summary_text}

@router.get("/summaries/{telegram_id}")
def get_user_summaries(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    summaries = get_summaries(user["id"])
    result = []
    for s in summaries:
        result.append({
            "id": s["id"],
            "title": s["title"],
            "subject": s["subject"] or "—",
            "date": s["created_at"][:10]
        })
    return {"summaries": result}

@router.get("/summaries/{telegram_id}/{summary_id}")
def get_single_summary(telegram_id: int, summary_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    summary = get_summary(summary_id)
    if not summary:
        raise HTTPException(status_code=404, detail="خلاصه پیدا نشد")
        
    return {
        "id": summary["id"],
        "title": summary["title"],
        "subject": summary["subject"] or "—",
        "text": summary["summary_text"],
        "date": summary["created_at"][:10]
    }

@router.delete("/summaries/{telegram_id}/{summary_id}")
def delete_user_summary(telegram_id: int, summary_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    delete_summary(summary_id)
    return {"status": "success"}

# ============================================================
# ستاره‌ها
# ============================================================
@router.get("/stars/{telegram_id}")
def get_stars_info(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    stars = get_user_stars(user["id"])
    claimed = get_claimed_star_rewards(user["id"])
    next_milestone, current = get_next_star_milestone(user["id"])
    month_display = get_jalali_month_display()
    days_left = get_days_until_month_end()
    
    rewards = []
    for milestone, points in sorted(STAR_REWARDS.items()):
        rewards.append({
            "milestone": milestone,
            "points": points,
            "claimed": milestone in claimed,
            "achieved": stars >= milestone,
            "remaining": max(0, milestone - stars)
        })
        
    return {
        "stars": stars,
        "month_display": month_display,
        "days_left": days_left,
        "next_milestone": next_milestone,
        "rewards": rewards
    }

# ============================================================
# دعوت دوستان
# ============================================================
@router.get("/referral/{telegram_id}")
def get_referral_info(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    if not user["has_purchased"]:
        return {"has_purchased": False}
        
    if not user["referral_code"]:
        code = generate_referral_code()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET referral_code = ? WHERE id = ?", (code, user["id"]))
        conn.commit()
        conn.close()
        user = get_user(telegram_id)
        
    stats = get_user_referral_stats(user["id"])
    available_discount = get_total_referral_discount(user["id"])
    
    return {
        "has_purchased": True,
        "referral_code": user["referral_code"],
        "total_invited": stats["total"],
        "successful": stats["successful"],
        "discount": available_discount
    }

# ============================================================
# اشتراک
# ============================================================
@router.get("/subscription/{telegram_id}")
def get_subscription_info(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    plans = []
    for key in ["bronze", "silver", "gold"]:
        info = PLAN_FEATURES[key]
        plans.append({
            "key": key,
            "name": PLAN_NAMES[key],
            "tagline": info["tagline"],
            "features": info["features"],
            "color": info["color"],
            "icon": info["icon"],
        })
        
    return {
        "plans": plans,
        "durations": [
            {"key": "1m", "name": DURATION_NAMES["1m"]},
            {"key": "3m", "name": DURATION_NAMES["3m"]},
            {"key": "6m", "name": DURATION_NAMES["6m"]},
            {"key": "12m", "name": DURATION_NAMES["12m"]},
        ]
    }

@router.get("/subscription/price/{plan_key}/{duration_key}")
def get_price(plan_key: str, duration_key: str, telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    details = calculate_purchase(user["id"], plan_key, duration_key)
    if not details:
        raise HTTPException(status_code=400, detail="خطا در محاسبه قیمت")
        
    return details

@router.post("/subscription/pay/{telegram_id}")
def start_payment(telegram_id: int, req: PaymentStart):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    details = calculate_purchase(user["id"], req.plan_key, req.duration_key)
    if not details:
        raise HTTPException(status_code=400, detail="خطا در محاسبه قیمت")
        
    request_id = create_payment_request(
        user["id"], req.plan_key, req.duration_key,
        details["base_price"], details["total_discount_percent"],
        details["coins_used"], details["final_price_toman"]
    )
    
    return {
        "request_id": request_id,
        "final_price": details["final_price_toman"]
    }

# ============================================================
# وضعیت پرداخت کاربر
# ============================================================
@router.get("/payment/status/{telegram_id}")
def get_user_payment_status(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    payments = get_user_payments(user["id"], limit=10)
    
    result = []
    for p in payments:
        result.append({
            "id": p["id"],
            "plan_key": p["plan_key"],
            "duration_key": p["duration_key"],
            "final_price": p["final_price"],
            "status": p["status"],
            "admin_note": p["admin_note"] or "",
            "sender_card": p["sender_card"],
            "tracking_code": p["tracking_code"],
            "created_at": p["created_at"][:16],
            "decided_at": p["decided_at"][:16] if p["decided_at"] else None,
        })
        
    return {"payments": result}

# ============================================================
# ثبت رسید پرداخت
# ============================================================
@router.post("/payment/submit-receipt/{request_id}")
def submit_receipt(request_id: int, req: PaymentReceiptSubmit, telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    payment = get_payment_request(request_id)
    if not payment:
        raise HTTPException(status_code=404, detail="درخواست پرداخت پیدا نشد")
        
    if payment["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="این درخواست متعلق به شما نیست")
        
    if payment["status"] != "pending":
        raise HTTPException(status_code=400, detail="این درخواست دیگه قابل ویرایش نیست")
        
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE payment_requests
        SET sender_card = ?, tracking_code = ?
        WHERE id = ?
    """, (req.sender_card, req.tracking_code, request_id))
    conn.commit()
    conn.close()
    
    return {"status": "success", "message": "اطلاعات رسید با موفقیت ثبت شد"}

# ============================================================
# ادمین پرداخت
# ============================================================
@router.get("/admin/payments/pending")
def admin_get_pending_payments(admin_id: int):
    if admin_id != ADMIN_ID:
        raise HTTPException(status_code=403, detail="شما ادمین نیستید")
        
    payments = get_pending_payments()
    result = []
    for p in payments:
        result.append({
            "id": p["id"],
            "user_id": p["user_id"],
            "first_name": p["first_name"],
            "telegram_id": p["telegram_id"],
            "username": p["username"] or "",
            "plan_key": p["plan_key"],
            "duration_key": p["duration_key"],
            "base_price": p["base_price"],
            "discount_percent": p["discount_percent"],
            "coin_used": p["coin_used"],
            "final_price": p["final_price"],
            "sender_card": p["sender_card"],
            "tracking_code": p["tracking_code"],
            "created_at": p["created_at"][:16],
        })
        
    return {"payments": result}

@router.get("/admin/payments/all")
def admin_get_all_payments(admin_id: int):
    if admin_id != ADMIN_ID:
        raise HTTPException(status_code=403, detail="شما ادمین نیستید")
        
    payments = get_all_payments(limit=100)
    result = []
    for p in payments:
        result.append({
            "id": p["id"],
            "first_name": p["first_name"],
            "telegram_id": p["telegram_id"],
            "plan_key": p["plan_key"],
            "duration_key": p["duration_key"],
            "final_price": p["final_price"],
            "status": p["status"],
            "sender_card": p["sender_card"],
            "tracking_code": p["tracking_code"],
            "created_at": p["created_at"][:16],
            "decided_at": p["decided_at"][:16] if p["decided_at"] else None,
        })
        
    return {"payments": result}

@router.post("/admin/payments/approve/{request_id}")
def admin_approve_payment(request_id: int, action: PaymentAction):
    if action.admin_id != ADMIN_ID:
        raise HTTPException(status_code=403, detail="شما ادمین نیستید")
        
    result = approve_payment(request_id, action.admin_id)
    if not result:
        raise HTTPException(status_code=404, detail="درخواست پیدا نشد")
        
    return {"status": "success", "message": "پرداخت تایید شد"}

@router.post("/admin/payments/reject/{request_id}")
def admin_reject_payment(request_id: int, action: PaymentAction):
    if action.admin_id != ADMIN_ID:
        raise HTTPException(status_code=403, detail="شما ادمین نیستید")
        
    req = get_payment_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="درخواست پیدا نشد")
        
    reject_payment(request_id, action.admin_id, action.note)
    return {"status": "success", "message": "پرداخت رد شد"}

# ============================================================
# اعلان پرداخت کاربر
# ============================================================
@router.get("/payment/unseen-count/{telegram_id}")
def get_payment_unseen_count(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    count = get_unseen_payment_count(user["id"])
    return {"count": count}

@router.post("/payment/mark-seen/{telegram_id}")
def mark_user_payments_seen(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    mark_payments_seen(user["id"])
    return {"status": "success"}

# ============================================================
# گروه مطالعه
# ============================================================
@router.get("/groups/{telegram_id}")
def get_groups_info(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    group = get_user_group(user["id"])
    
    if not group:
        return {
            "in_group": False,
            "max_members": GROUP_MAX_MEMBERS,
            "challenge_types": [
                {"key": k, "name": v["name"], "unit": v["unit"], "default_goal": v["default_goal"]}
                for k, v in GROUP_CHALLENGE_TYPES.items()
            ],
            "challenge_durations": [
                {"key": k, "name": v["name"], "days": v["days"]}
                for k, v in GROUP_CHALLENGE_DURATIONS.items()
            ]
        }
        
    members = get_group_members(group["id"])
    is_owner = is_group_owner(group["id"], user["id"])
    challenge = get_group_challenge(group["id"])
    progress = None
    
    challenge_data = None
    if challenge:
        progress = get_challenge_progress(group["id"])
        type_info = GROUP_CHALLENGE_TYPES.get(challenge["challenge_type"], {})
        duration_info = GROUP_CHALLENGE_DURATIONS.get(challenge["duration_type"], {})
        challenge_data = {
            "type": challenge["challenge_type"],
            "type_name": type_info.get("name", challenge["challenge_type"]),
            "unit": type_info.get("unit", ""),
            "goal": challenge["goal_value"],
            "duration_type": challenge["duration_type"],
            "duration_name": duration_info.get("name", challenge["duration_type"]),
            "start_date": challenge["start_date"],
            "end_date": challenge["end_date"],
            "current": progress["current"] if progress else 0,
            "percent": progress["percent"] if progress else 0,
        }
        
    members_sorted = sorted(members, key=lambda m: m["league_points"], reverse=True)
    members_data = []
    for i, m in enumerate(members_sorted):
        hours = m["study_minutes"] // 60
        minutes = m["study_minutes"] % 60
        if hours > 0:
            study_str = f"{hours}س {minutes}د"
        else:
            study_str = f"{minutes}د"
            
        members_data.append({
            "rank": i + 1,
            "name": m["first_name"],
            "telegram_id": m["telegram_id"],
            "league_points": m["league_points"],
            "study_str": study_str,
            "is_me": m["id"] == user["id"],
            "is_owner": m["id"] == group["owner_id"],
        })
        
    total_points = sum(m["league_points"] for m in members)
    total_minutes = sum(m["study_minutes"] for m in members)
    total_hours = total_minutes // 60
    
    return {
        "in_group": True,
        "group": {
            "id": group["id"],
            "name": group["name"],
            "code": group["code"],
            "owner_id": group["owner_id"],
            "created_at": group["created_at"][:10],
        },
        "is_owner": is_owner,
        "members_count": len(members),
        "max_members": GROUP_MAX_MEMBERS,
        "members": members_data,
        "challenge": challenge_data,
        "total_points": total_points,
        "total_hours": total_hours,
        "challenge_types": [
            {"key": k, "name": v["name"], "unit": v["unit"], "default_goal": v["default_goal"]}
            for k, v in GROUP_CHALLENGE_TYPES.items()
        ] if is_owner else [],
        "challenge_durations": [
            {"key": k, "name": v["name"], "days": v["days"]}
            for k, v in GROUP_CHALLENGE_DURATIONS.items()
        ] if is_owner else []
    }

@router.post("/groups/create/{telegram_id}")
def create_new_group(telegram_id: int, req: GroupCreate):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    if not req.name or len(req.name.strip()) < 2:
        raise HTTPException(status_code=400, detail="اسم گروه باید حداقل ۲ کاراکتر باشه")
        
    existing = get_user_group(user["id"])
    if existing:
        raise HTTPException(status_code=400, detail="شما قبلاً توی یه گروه هستید")
        
    result = create_group(req.name.strip(), user["id"])
    if not result:
        raise HTTPException(status_code=400, detail="خطا در ساخت گروه")
        
    group_id, code = result
    return {"status": "success", "group_id": group_id, "code": code}

@router.post("/groups/join/{telegram_id}")
def join_existing_group(telegram_id: int, req: GroupJoin):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    code = req.code.strip()
    if not code or len(code) != 6 or not code.isdigit():
        raise HTTPException(status_code=400, detail="کد گروه باید ۶ رقم باشه")
        
    status, message = join_group(code, user["id"])
    
    if status == "success":
        return {"status": "success", "message": message}
    elif status == "already_member":
        return {"status": "already_member", "message": "شما همین الان عضو این گروه هستید"}
    elif status == "already_in_group":
        raise HTTPException(status_code=400, detail=message)
    elif status == "full":
        raise HTTPException(status_code=400, detail=message)
    else:
        raise HTTPException(status_code=404, detail=message)

@router.post("/groups/leave/{telegram_id}")
def leave_current_group(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    status, group_name = leave_group(user["id"])
    
    if status == "not_in_group":
        raise HTTPException(status_code=400, detail="شما توی هیچ گروهی نیستید")
    elif status == "owner_left":
        return {"status": "success", "message": f"گروه «{group_name}» حذف شد"}
    else:
        return {"status": "success", "message": f"از گروه «{group_name}» خارج شدید"}

@router.post("/groups/challenge/create/{telegram_id}")
def create_challenge(telegram_id: int, req: ChallengeCreate):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    group = get_user_group(user["id"])
    if not group:
        raise HTTPException(status_code=400, detail="شما توی هیچ گروهی نیستید")
        
    if not is_group_owner(group["id"], user["id"]):
        raise HTTPException(status_code=403, detail="فقط مالک گروه می‌تونه چالش بسازه")
        
    if get_group_challenge(group["id"]):
        raise HTTPException(status_code=400, detail="این گروه یه چالش فعال داره")
        
    if req.challenge_type not in GROUP_CHALLENGE_TYPES:
        raise HTTPException(status_code=400, detail="نوع چالش نامعتبره")
        
    if req.duration_type not in GROUP_CHALLENGE_DURATIONS:
        raise HTTPException(status_code=400, detail="مدت چالش نامعتبره")
        
    if req.goal_value < 1:
        raise HTTPException(status_code=400, detail="هدف چالش باید حداقل ۱ باشه")
        
    challenge_id = create_group_challenge(
        group["id"], req.challenge_type, req.goal_value,
        req.duration_type, user["id"]
    )
    
    if not challenge_id:
        raise HTTPException(status_code=400, detail="خطا در ساخت چالش")
        
    return {"status": "success", "challenge_id": challenge_id}

@router.post("/groups/challenge/cancel/{telegram_id}")
def cancel_challenge(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    group = get_user_group(user["id"])
    if not group:
        raise HTTPException(status_code=400, detail="شما توی هیچ گروهی نیستید")
        
    if not is_group_owner(group["id"], user["id"]):
        raise HTTPException(status_code=403, detail="فقط مالک گروه می‌تونه چالش رو لغو کنه")
        
    if not get_group_challenge(group["id"]):
        raise HTTPException(status_code=400, detail="چالش فعالی وجود نداره")
        
    cancel_group_challenge(group["id"])
    return {"status": "success", "message": "چالش لغو شد"}

# ============================================================
# نبرد ۱ به ۱
# ============================================================
@router.get("/battle/subjects/{telegram_id}")
def get_battle_subjects(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    if user["coins"] < BATTLE_WAGER:
        raise HTTPException(status_code=400, detail=f"برای نبرد حداقل {BATTLE_WAGER} سکه لازمه")
        
    subjects = get_subjects(user["id"])
    result = []
    for s in subjects:
        result.append({"id": s["id"], "book": s["book"], "grade": s["grade"], "field": s["field"]})
        
    return {
        "subjects": result,
        "wager": BATTLE_WAGER,
        "questions_count": BATTLE_QUESTIONS,
    }

@router.post("/battle/create/{telegram_id}")
def create_new_battle(telegram_id: int, req: BattleCreate):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    if user["coins"] < BATTLE_WAGER:
        raise HTTPException(status_code=400, detail=f"برای نبرد حداقل {BATTLE_WAGER} سکه لازمه")
        
    subject = get_subject(req.subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="درس پیدا نشد")
        
    add_coins(user["id"], -BATTLE_WAGER)
    
    questions = generate_battle_questions(
        subject["book"], subject["grade"], subject["field"],
        BATTLE_QUESTIONS
    )
    if not questions:
        add_coins(user["id"], BATTLE_WAGER)
        raise HTTPException(status_code=500, detail="خطا در ساخت سوالات")
        
    correct_answers = [q['answer'] for q in questions]
    code = generate_battle_code()
    
    battle_id = create_battle(
        user["id"], code, questions, correct_answers, BATTLE_WAGER
    )
    
    return {
        "status": "success",
        "battle_id": battle_id,
        "code": code,
        "subject_book": subject["book"],
        "wager": BATTLE_WAGER,
    }

@router.post("/battle/join/{telegram_id}")
def join_existing_battle(telegram_id: int, req: BattleJoin):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    if user["coins"] < BATTLE_WAGER:
        raise HTTPException(status_code=400, detail=f"برای نبرد حداقل {BATTLE_WAGER} سکه لازمه")
        
    code = req.code.strip()
    if not code or len(code) != 6:
        raise HTTPException(status_code=400, detail="کد نبرد باید ۶ رقم باشه")
        
    battle = get_battle_by_code(code)
    if not battle:
        raise HTTPException(status_code=404, detail="نبردی با این کد پیدا نشد")
        
    if battle["status"] != "waiting":
        raise HTTPException(status_code=400, detail="این نبرد دیگه قابل پیوستن نیست")
        
    if battle["creator_id"] == user["id"]:
        raise HTTPException(status_code=400, detail="نمی‌تونی به نبرد خودت بپیوندی")
        
    add_coins(user["id"], -BATTLE_WAGER)
    
    success = join_battle(battle["id"], user["id"])
    if not success:
        add_coins(user["id"], BATTLE_WAGER)
        raise HTTPException(status_code=400, detail="خطا در پیوستن به نبرد")
        
    return {"status": "success", "battle_id": battle["id"]}

@router.get("/battle/status/{battle_id}/{telegram_id}")
def get_battle_status(battle_id: int, telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    battle = get_battle(battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="نبرد پیدا نشد")
        
    if battle["creator_id"] != user["id"] and battle["opponent_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="شما در این نبرد نیستید")
        
    is_creator = battle["creator_id"] == user["id"]
    
    creator = get_user_by_id(battle["creator_id"])
    opponent = get_user_by_id(battle["opponent_id"]) if battle["opponent_id"] else None
    
    result = {
        "battle_id": battle["id"],
        "code": battle["code"],
        "status": battle["status"],
        "is_creator": is_creator,
        "wager": battle["wager"],
        "creator_name": creator["first_name"] if creator else "—",
        "opponent_name": opponent["first_name"] if opponent else None,
        "creator_answered": battle["creator_answers"] is not None,
        "opponent_answered": battle["opponent_answers"] is not None,
    }
    
    if battle["status"] == "active":
        questions = json.loads(battle["questions"])
        my_answers = battle["creator_answers"] if is_creator else battle["opponent_answers"]
        if my_answers is None:
            result["questions"] = questions
            result["need_answers"] = True
        else:
            result["need_answers"] = False
    
    if battle["status"] == "completed":
        result["creator_correct"] = battle["creator_correct"]
        result["opponent_correct"] = battle["opponent_correct"]
        result["winner_id"] = battle["winner_id"]
        result["i_won"] = battle["winner_id"] == user["id"]
        result["i_am_creator"] = is_creator
        
    return result

@router.post("/battle/submit/{battle_id}/{telegram_id}")
def submit_battle_answers(battle_id: int, telegram_id: int, req: BattleAnswers):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    battle = get_battle(battle_id)
    if not battle:
        raise HTTPException(status_code=404, detail="نبرد پیدا نشد")
        
    if battle["status"] != "active":
        raise HTTPException(status_code=400, detail="این نبرد فعال نیست")
        
    is_creator = battle["creator_id"] == user["id"]
    is_opponent = battle["opponent_id"] == user["id"]
    
    if not is_creator and not is_opponent:
        raise HTTPException(status_code=403, detail="شما در این نبرد نیستید")
        
    side = "creator" if is_creator else "opponent"
    field = f"{side}_answers"
    
    if battle[field] is not None:
        raise HTTPException(status_code=400, detail="قبلاً جواب‌هات رو ارسال کردی")
        
    save_battle_answer(battle_id, side, req.answers)
    
    battle = get_battle(battle_id) 
    if battle["creator_answers"] is not None and battle["opponent_answers"] is not None:
        correct = json.loads(battle["correct_answers"])
        creator_answers = json.loads(battle["creator_answers"])
        opponent_answers = json.loads(battle["opponent_answers"])
        
        creator_correct = sum(1 for i, c in enumerate(correct) if i < len(creator_answers) and creator_answers[i] == c)
        opponent_correct = sum(1 for i, c in enumerate(correct) if i < len(opponent_answers) and opponent_answers[i] == c)
        
        if creator_correct > opponent_correct:
            winner_id = battle["creator_id"]
        elif opponent_correct > creator_correct:
            winner_id = battle["opponent_id"]
        else:
            winner_id = None
        
        complete_battle(battle_id, creator_correct, opponent_correct, winner_id)
        
        if winner_id:
            add_coins(winner_id, BATTLE_WAGER * 2)
            add_league_points(winner_id, LEAGUE_POINTS["battle_win"])
        else:
            add_coins(battle["creator_id"], BATTLE_WAGER)
            add_coins(battle["opponent_id"], BATTLE_WAGER)
        
        return {"status": "success", "completed": True}
    
    return {"status": "success", "completed": False, "waiting_for_other": True}

@router.get("/battle/history/{telegram_id}")
def get_battle_history(telegram_id: int):
    user = get_user(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    battles = get_user_battle_history(user["id"], limit=20)
    result = []
    for b in battles:
        is_creator = b["creator_id"] == user["id"]
        my_correct = b["creator_correct"] if is_creator else b["opponent_correct"]
        opp_correct = b["opponent_correct"] if is_creator else b["creator_correct"]
        
        opp_id = b["opponent_id"] if is_creator else b["creator_id"]
        opp_user = get_user_by_id(opp_id) if opp_id else None
        
        result.append({
            "id": b["id"],
            "opponent_name": opp_user["first_name"] if opp_user else "—",
            "my_correct": my_correct,
            "opp_correct": opp_correct,
            "won": b["winner_id"] == user["id"],
            "tie": b["winner_id"] is None,
            "date": b["completed_at"][:10] if b["completed_at"] else "—",
        })
        
    return {"history": result}
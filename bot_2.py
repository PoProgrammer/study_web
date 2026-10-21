import json
import sqlite3
import random
import string
from datetime import datetime, timedelta
import jdatetime

from config import (
    ACHIEVEMENTS, DAILY_QUESTS, COINS_PER_ACHIEVEMENT,
)

from bot_1 import (
    DB_FILE,
    LEAGUE_GRADES, LEAGUE_PRIZES, LEAGUE_POINTS,
    BATTLE_WAGER, BATTLE_QUESTIONS,
    STAR_REWARDS,
    GROUP_MAX_MEMBERS,
    GROUP_CODE_LENGTH,
    GROUP_CHALLENGE_TYPES,
    GROUP_CHALLENGE_DURATIONS,
    PLAN_PRICES_TOMAN,
    COIN_DISCOUNT_PERCENT,
    REFERRAL_DISCOUNT_PERCENT,
    REFERRED_DISCOUNT_PERCENT,
    MAX_TOTAL_DISCOUNT_PERCENT,
    COIN_TO_TOMAN,
    COINS_EXAM_90_PLUS,
    COINS_MOCK_EXAM,
    COINS_BATTLE_WIN,
)


# ============================================================
# توابع کمکی تاریخ
# ============================================================
def get_jalali_month_key():
    today = jdatetime.date.today()
    return f"{today.year}-{today.month:02d}"


def get_jalali_month_display():
    today = jdatetime.date.today()
    month_names = [
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
    ]
    return f"{month_names[today.month - 1]} {today.year}"


def get_days_until_month_end():
    today = jdatetime.date.today()
    if today.month <= 6:
        days_in_month = 31
    elif today.month <= 11:
        days_in_month = 30
    else:
        days_in_month = 30 if today.isleap() else 29
    return days_in_month - today.day


def get_today_jalali():
    today = jdatetime.date.today()
    return today.strftime("%Y-%m-%d")


# ============================================================
# اتصال
# ============================================================
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# ساخت جداول
# ============================================================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            first_name TEXT,
            username TEXT,
            coins INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            last_study_date TEXT,
            joined_at TEXT,
            plan TEXT DEFAULT 'free',
            plan_expires_at TEXT,
            grade TEXT,
            field TEXT,
            referral_code TEXT UNIQUE,
            referred_by INTEGER,
            has_purchased INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            grade TEXT,
            field TEXT,
            book TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject_id INTEGER,
            chapter TEXT,
            topics TEXT,
            duration INTEGER,
            start_time TEXT,
            end_time TEXT,
            status TEXT DEFAULT 'active'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject_id INTEGER,
            chapter TEXT,
            questions TEXT,
            user_answers TEXT,
            correct_answers TEXT,
            score INTEGER,
            coins_earned INTEGER,
            status TEXT DEFAULT 'active',
            started_at TEXT,
            completed_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            goal TEXT,
            subjects TEXT,
            hours_per_day REAL,
            off_days TEXT,
            plan_text TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            exams_count INTEGER DEFAULT 0,
            ai_count INTEGER DEFAULT 0,
            summary_count INTEGER DEFAULT 0,
            analysis_count INTEGER DEFAULT 0,
            plan_count INTEGER DEFAULT 0,
            UNIQUE(user_id, date)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            achievement_id TEXT,
            earned_at TEXT,
            UNIQUE(user_id, achievement_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            quest_id TEXT,
            completed INTEGER DEFAULT 0,
            claimed INTEGER DEFAULT 0,
            UNIQUE(user_id, date, quest_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS question_bank (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            subject_id INTEGER,
            chapter TEXT,
            grade TEXT,
            field TEXT,
            book TEXT,
            question_text TEXT,
            options TEXT,
            correct_answer INTEGER,
            user_answer INTEGER,
            added_at TEXT,
            times_wrong INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            subject TEXT,
            summary_text TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mock_exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            exam_type TEXT,
            total_questions INTEGER,
            duration_minutes INTEGER,
            books_json TEXT,
            questions TEXT,
            user_answers TEXT,
            correct_answers TEXT,
            results_by_book TEXT,
            total_correct INTEGER,
            total_wrong INTEGER,
            total_blank INTEGER,
            percent REAL,
            coins_earned INTEGER,
            status TEXT DEFAULT 'active',
            started_at TEXT,
            completed_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS battles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            creator_id INTEGER,
            opponent_id INTEGER,
            questions TEXT,
            correct_answers TEXT,
            creator_answers TEXT,
            opponent_answers TEXT,
            creator_correct INTEGER DEFAULT 0,
            opponent_correct INTEGER DEFAULT 0,
            wager INTEGER DEFAULT 10,
            winner_id INTEGER,
            status TEXT DEFAULT 'waiting',
            created_at TEXT,
            started_at TEXT,
            completed_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS league_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            month_key TEXT,
            points INTEGER DEFAULT 0,
            UNIQUE(user_id, month_key)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS league_winners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            month_key TEXT,
            rank INTEGER,
            points INTEGER,
            coins_won INTEGER,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_stars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            month_key TEXT,
            UNIQUE(user_id, date)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS star_rewards_claimed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            month_key TEXT,
            milestone INTEGER,
            claimed_at TEXT,
            UNIQUE(user_id, month_key, milestone)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS study_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            code TEXT UNIQUE,
            owner_id INTEGER,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER,
            user_id INTEGER UNIQUE,
            joined_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_challenges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER UNIQUE,
            challenge_type TEXT,
            goal_value INTEGER,
            duration_type TEXT,
            start_date TEXT,
            end_date TEXT,
            created_by INTEGER,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payment_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            plan_key TEXT,
            duration_key TEXT,
            base_price INTEGER,
            discount_percent INTEGER,
            coin_used INTEGER,
            final_price INTEGER,
            receipt_file_id TEXT,
            status TEXT DEFAULT 'pending',
            admin_note TEXT,
            created_at TEXT,
            decided_at TEXT,
            decided_by INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_discounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            discount_percent INTEGER,
            source TEXT,
            used INTEGER DEFAULT 0,
            created_at TEXT,
            used_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER,
            referred_id INTEGER UNIQUE,
            registered_at TEXT,
            first_purchase_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS support_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            sender TEXT,
            message_text TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    # ===== جداول جدید برای تاریخچه چت و برنامه‌ریزی =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT,
            message_text TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            goal TEXT,
            subjects TEXT,
            hours REAL,
            off_days TEXT,
            plan_text TEXT,
            created_at TEXT
        )
    """)

    # Migrations
    cursor.execute("PRAGMA table_info(users)")
    user_cols = [row[1] for row in cursor.fetchall()]
    if "grade" not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN grade TEXT")
    if "field" not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN field TEXT")
    if "referral_code" not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN referral_code TEXT")
    if "referred_by" not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN referred_by INTEGER")
    if "has_purchased" not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN has_purchased INTEGER DEFAULT 0")
    if "password_hash" not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
    if "avatar" not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN avatar TEXT DEFAULT '🦊'")

    cursor.execute("PRAGMA table_info(league_points)")
    lp_cols = [row[1] for row in cursor.fetchall()]
    if "month_key" not in lp_cols:
        cursor.execute("ALTER TABLE league_points ADD COLUMN month_key TEXT")

    cursor.execute("PRAGMA table_info(league_winners)")
    lw_cols = [row[1] for row in cursor.fetchall()]
    if "month_key" not in lw_cols:
        cursor.execute("ALTER TABLE league_winners ADD COLUMN month_key TEXT")

    cursor.execute("PRAGMA table_info(user_stars)")
    us_cols = [row[1] for row in cursor.fetchall()]
    if "month_key" not in us_cols:
        cursor.execute("ALTER TABLE user_stars ADD COLUMN month_key TEXT")

    cursor.execute("PRAGMA table_info(star_rewards_claimed)")
    src_cols = [row[1] for row in cursor.fetchall()]
    if "month_key" not in src_cols:
        cursor.execute("ALTER TABLE star_rewards_claimed ADD COLUMN month_key TEXT")

    cursor.execute("PRAGMA table_info(daily_usage)")
    du_cols = [row[1] for row in cursor.fetchall()]
    if "summary_count" not in du_cols:
        cursor.execute("ALTER TABLE daily_usage ADD COLUMN summary_count INTEGER DEFAULT 0")
    if "analysis_count" not in du_cols:
        cursor.execute("ALTER TABLE daily_usage ADD COLUMN analysis_count INTEGER DEFAULT 0")
    if "plan_count" not in du_cols:
        cursor.execute("ALTER TABLE daily_usage ADD COLUMN plan_count INTEGER DEFAULT 0")

    # Migration: payment_requests
    cursor.execute("PRAGMA table_info(payment_requests)")
    pr_cols = [row[1] for row in cursor.fetchall()]
    if "user_seen" not in pr_cols:
        cursor.execute("ALTER TABLE payment_requests ADD COLUMN user_seen INTEGER DEFAULT 1")
    if "sender_card" not in pr_cols:
        cursor.execute("ALTER TABLE payment_requests ADD COLUMN sender_card TEXT")
    if "tracking_code" not in pr_cols:
        cursor.execute("ALTER TABLE payment_requests ADD COLUMN tracking_code TEXT")

    conn.commit()
    conn.close()
# ============================================================
# کاربر
# ============================================================
def generate_referral_code():
    conn = get_db()
    cursor = conn.cursor()
    for _ in range(50):
        code = 'REF' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        cursor.execute("SELECT id FROM users WHERE referral_code = ?", (code,))
        if not cursor.fetchone():
            conn.close()
            return code
    conn.close()
    return 'REF' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def save_user(telegram_id, first_name, username):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO users (telegram_id, first_name, username, coins, streak, joined_at, plan)
        VALUES (?, ?, ?, 0, 0, ?, 'free')
    """, (telegram_id, first_name, username or "", datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_user(telegram_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


def set_user_grade(user_id, grade):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET grade = ? WHERE id = ?", (grade, user_id))
    conn.commit()
    conn.close()


def get_user_grade(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT grade FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row['grade'] if row and row['grade'] else None


def set_user_field(user_id, field):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET field = ? WHERE id = ?", (field, user_id))
    conn.commit()
    conn.close()


def get_user_field(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT field FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row['field'] if row and row['field'] else None


def add_coins(user_id, amount):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coins = coins + ? WHERE id = ?", (amount, user_id))
    conn.commit()
    conn.close()


def reset_coins(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coins = 0 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_current_plan(user):
    plan_key = user['plan'] or 'free'
    if plan_key == 'free':
        return 'free'
    expires_at = user['plan_expires_at']
    if not expires_at:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET plan='free', plan_expires_at=NULL WHERE id=?", (user['id'],))
        conn.commit()
        conn.close()
        return 'free'
    try:
        exp = datetime.fromisoformat(expires_at)
        if datetime.now() >= exp:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET plan='free', plan_expires_at=NULL WHERE id=?", (user['id'],))
            conn.commit()
            conn.close()
            return 'free'
    except Exception:
        return 'free'
    return plan_key


def set_plan(user_id, plan_key, days):
    expires = datetime.now() + timedelta(days=days)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET plan=?, plan_expires_at=? WHERE id=?
    """, (plan_key, expires.isoformat(), user_id))
    conn.commit()
    conn.close()


def get_plan_price_toman(plan_key, duration_key):
    return PLAN_PRICES_TOMAN.get(plan_key, {}).get(duration_key, 0)


def get_plan_days(duration_key):
    return {"1m": 30, "3m": 90, "6m": 180, "12m": 365}.get(duration_key, 30)


# ============================================================
# سیستم تخفیف
# ============================================================
def add_user_discount(user_id, percent, source="referral"):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_discounts (user_id, discount_percent, source, used, created_at)
        VALUES (?, ?, ?, 0, ?)
    """, (user_id, percent, source, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_user_discounts(user_id, include_used=False):
    conn = get_db()
    cursor = conn.cursor()
    if include_used:
        cursor.execute("SELECT * FROM user_discounts WHERE user_id = ? ORDER BY id DESC", (user_id,))
    else:
        cursor.execute("SELECT * FROM user_discounts WHERE user_id = ? AND used = 0 ORDER BY id DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_total_referral_discount(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT SUM(discount_percent) as total FROM user_discounts
        WHERE user_id = ? AND used = 0
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row['total'] or 0


def mark_user_discounts_used(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE user_discounts SET used = 1, used_at = ?
        WHERE user_id = ? AND used = 0
    """, (datetime.now().isoformat(), user_id))
    conn.commit()
    conn.close()


def calculate_purchase(user_id, plan_key, duration_key):
    user = get_user_by_id(user_id)
    if not user:
        return None
    base_price = get_plan_price_toman(plan_key, duration_key)
    if base_price == 0:
        return None
    user_coins = user['coins']
    max_coin_discount = int(base_price * COIN_DISCOUNT_PERCENT / 100)
    max_coins_needed = max_coin_discount // COIN_TO_TOMAN
    coins_to_use = min(user_coins, max_coins_needed)
    coin_discount_toman = coins_to_use * COIN_TO_TOMAN
    referral_percent = get_total_referral_discount(user_id)
    referral_discount_toman = int(base_price * referral_percent / 100)
    referred_discount_toman = 0
    if user['referred_by'] and not user['has_purchased']:
        referred_discount_toman = int(base_price * REFERRED_DISCOUNT_PERCENT / 100)
    total_discount_toman = coin_discount_toman + referral_discount_toman + referred_discount_toman
    max_discount = base_price
    if total_discount_toman > max_discount:
        total_discount_toman = max_discount
    final_price_toman = base_price - total_discount_toman
    total_discount_percent = int((total_discount_toman / base_price) * 100) if base_price > 0 else 0
    return {
        "base_price": base_price,
        "coins_used": coins_to_use,
        "coin_discount_toman": coin_discount_toman,
        "referral_percent": referral_percent,
        "referral_discount_toman": referral_discount_toman,
        "referred_discount_toman": referred_discount_toman,
        "total_discount_toman": total_discount_toman,
        "total_discount_percent": total_discount_percent,
        "final_price_toman": final_price_toman,
    }


# ============================================================
# ستاره روزانه
# ============================================================
def register_daily_star(user_id):
    today = get_today_jalali()
    month_key = get_jalali_month_key()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO user_stars (user_id, date, month_key)
        VALUES (?, ?, ?)
    """, (user_id, today, month_key))
    conn.commit()
    inserted = cursor.rowcount > 0
    conn.close()
    return inserted


def get_user_stars(user_id, month_key=None):
    if month_key is None:
        month_key = get_jalali_month_key()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as c FROM user_stars
        WHERE user_id = ? AND month_key = ?
    """, (user_id, month_key))
    count = cursor.fetchone()['c']
    conn.close()
    return count


def get_claimed_star_rewards(user_id, month_key=None):
    if month_key is None:
        month_key = get_jalali_month_key()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT milestone FROM star_rewards_claimed
        WHERE user_id = ? AND month_key = ?
    """, (user_id, month_key))
    rows = cursor.fetchall()
    conn.close()
    return {r['milestone'] for r in rows}


def check_and_claim_star_rewards(user_id):
    month_key = get_jalali_month_key()
    stars = get_user_stars(user_id, month_key)
    claimed = get_claimed_star_rewards(user_id, month_key)
    newly_earned = []
    for milestone, points in sorted(STAR_REWARDS.items()):
        if milestone in claimed:
            continue
        if stars >= milestone:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO star_rewards_claimed
                (user_id, month_key, milestone, claimed_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, month_key, milestone, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            add_league_points(user_id, points)
            newly_earned.append({"milestone": milestone, "points": points})
    return newly_earned


def get_next_star_milestone(user_id):
    stars = get_user_stars(user_id)
    claimed = get_claimed_star_rewards(user_id)
    for milestone in sorted(STAR_REWARDS.keys()):
        if milestone not in claimed:
            return milestone, stars
    return None, stars


# ============================================================
# لیگ
# ============================================================
def add_league_points(user_id, points):
    month_key = get_jalali_month_key()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO league_points (user_id, month_key, points)
        VALUES (?, ?, 0)
    """, (user_id, month_key))
    cursor.execute("""
        UPDATE league_points SET points = points + ?
        WHERE user_id = ? AND month_key = ?
    """, (points, user_id, month_key))
    conn.commit()
    conn.close()


def get_user_league_points(user_id):
    month_key = get_jalali_month_key()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT points FROM league_points WHERE user_id = ? AND month_key = ?", (user_id, month_key))
    row = cursor.fetchone()
    conn.close()
    return row['points'] if row else 0


def get_user_league_rank(user_id):
    grade = get_user_grade(user_id)
    if not grade:
        return 0
    month_key = get_jalali_month_key()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) + 1 as rank FROM league_points lp
        JOIN users u ON lp.user_id = u.id
        WHERE lp.month_key = ? AND u.grade = ? AND lp.points > (
            SELECT COALESCE(points, 0) FROM league_points
            WHERE user_id = ? AND month_key = ?
        )
    """, (month_key, grade, user_id, month_key))
    rank = cursor.fetchone()['rank']
    conn.close()
    return rank


def get_league_leaderboard(grade, limit=10):
    if grade not in LEAGUE_GRADES:
        return []
    month_key = get_jalali_month_key()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT lp.user_id, lp.points, u.first_name, u.coins
        FROM league_points lp
        JOIN users u ON lp.user_id = u.id
        WHERE lp.month_key = ? AND u.grade = ? AND lp.points > 0
        ORDER BY lp.points DESC LIMIT ?
    """, (month_key, grade, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_league_participants_count(grade):
    month_key = get_jalali_month_key()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as c FROM league_points lp
        JOIN users u ON lp.user_id = u.id
        WHERE lp.month_key = ? AND u.grade = ? AND lp.points > 0
    """, (month_key, grade))
    count = cursor.fetchone()['c']
    conn.close()
    return count


def finalize_league(month_key, grade):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as c FROM league_winners
        WHERE month_key = ? AND user_id IN (SELECT id FROM users WHERE grade = ?)
    """, (month_key, grade))
    if cursor.fetchone()['c'] > 0:
        conn.close()
        return None
    cursor.execute("""
        SELECT lp.user_id, lp.points, u.first_name
        FROM league_points lp
        JOIN users u ON lp.user_id = u.id
        WHERE lp.month_key = ? AND u.grade = ? AND lp.points > 0
        ORDER BY lp.points DESC LIMIT 3
    """, (month_key, grade))
    top3 = cursor.fetchall()
    conn.close()
    results = []
    for i, row in enumerate(top3):
        rank = i + 1
        coins = LEAGUE_PRIZES.get(rank, 0)
        add_coins(row['user_id'], coins)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO league_winners (user_id, month_key, rank, points, coins_won, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (row['user_id'], month_key, rank, row['points'], coins, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        results.append({
            "user_id": row['user_id'],
            "name": row['first_name'],
            "rank": rank,
            "points": row['points'],
            "coins": coins,
            "grade": grade,
        })
    return results


def get_user_league_history(user_id, limit=5):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM league_winners WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows


# ============================================================
# نبردها
# ============================================================
def create_battle(creator_id, code, questions, correct_answers, wager):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO battles (code, creator_id, questions, correct_answers, wager, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'waiting', ?)
    """, (code, creator_id, json.dumps(questions, ensure_ascii=False),
          json.dumps(correct_answers), wager, datetime.now().isoformat()))
    conn.commit()
    battle_id = cursor.lastrowid
    conn.close()
    return battle_id


def get_battle_by_code(code):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM battles WHERE code = ?", (code,))
    battle = cursor.fetchone()
    conn.close()
    return battle


def get_battle(battle_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM battles WHERE id = ?", (battle_id,))
    battle = cursor.fetchone()
    conn.close()
    return battle


def join_battle(battle_id, opponent_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE battles SET opponent_id = ?, status = 'active', started_at = ?
        WHERE id = ? AND status = 'waiting'
    """, (opponent_id, datetime.now().isoformat(), battle_id))
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0


def save_battle_answer(battle_id, side, answers):
    field = f"{side}_answers"
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE battles SET {field} = ? WHERE id = ?", (json.dumps(answers), battle_id))
    conn.commit()
    conn.close()


def complete_battle(battle_id, creator_correct, opponent_correct, winner_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE battles SET creator_correct = ?, opponent_correct = ?,
                          winner_id = ?, status = 'completed', completed_at = ?
        WHERE id = ?
    """, (creator_correct, opponent_correct, winner_id, datetime.now().isoformat(), battle_id))
    conn.commit()
    conn.close()


def get_user_battle_history(user_id, limit=10):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM battles
        WHERE (creator_id = ? OR opponent_id = ?) AND status = 'completed'
        ORDER BY id DESC LIMIT ?
    """, (user_id, user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows


# ============================================================
# مصرف روزانه
# ============================================================
def get_today_usage(user_id):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM daily_usage WHERE user_id = ? AND date = ?", (user_id, today))
    row = cursor.fetchone()
    conn.close()
    if not row:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO daily_usage
            (user_id, date, exams_count, ai_count, summary_count, analysis_count, plan_count)
            VALUES (?, ?, 0, 0, 0, 0, 0)
        """, (user_id, today))
        conn.commit()
        conn.close()
        return {"exams_count": 0, "ai_count": 0, "summary_count": 0, "analysis_count": 0, "plan_count": 0}
    return {
        "exams_count": row['exams_count'],
        "ai_count": row['ai_count'],
        "summary_count": row['summary_count'] if 'summary_count' in row.keys() else 0,
        "analysis_count": row['analysis_count'] if 'analysis_count' in row.keys() else 0,
        "plan_count": row['plan_count'] if 'plan_count' in row.keys() else 0,
    }


def _inc_usage_field(user_id, field):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO daily_usage
        (user_id, date, exams_count, ai_count, summary_count, analysis_count, plan_count)
        VALUES (?, ?, 0, 0, 0, 0, 0)
    """, (user_id, today))
    cursor.execute(f"""
        UPDATE daily_usage SET {field} = {field} + 1
        WHERE user_id = ? AND date = ?
    """, (user_id, today))
    conn.commit()
    conn.close()


def inc_exams_count(user_id):
    _inc_usage_field(user_id, "exams_count")


def inc_ai_count(user_id):
    _inc_usage_field(user_id, "ai_count")


def inc_summary_count(user_id):
    _inc_usage_field(user_id, "summary_count")


def inc_analysis_count(user_id):
    _inc_usage_field(user_id, "analysis_count")


def inc_plan_count(user_id):
    _inc_usage_field(user_id, "plan_count")


# ============================================================
# آزمون کنکور
# ============================================================
def save_mock_exam(user_id, exam_type, total_questions, duration_minutes, books_json, questions, correct_answers):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO mock_exams
        (user_id, exam_type, total_questions, duration_minutes, books_json,
         questions, correct_answers, status, started_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?)
    """, (user_id, exam_type, total_questions, duration_minutes,
          json.dumps(books_json, ensure_ascii=False),
          json.dumps(questions, ensure_ascii=False),
          json.dumps(correct_answers), datetime.now().isoformat()))
    conn.commit()
    exam_id = cursor.lastrowid
    conn.close()
    return exam_id


def complete_mock_exam(exam_id, user_answers, results_by_book, total_correct, total_wrong, total_blank, percent, coins):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE mock_exams
        SET user_answers = ?, results_by_book = ?,
            total_correct = ?, total_wrong = ?, total_blank = ?,
            percent = ?, coins_earned = ?, status = 'completed', completed_at = ?
        WHERE id = ?
    """, (json.dumps(user_answers), json.dumps(results_by_book, ensure_ascii=False),
          total_correct, total_wrong, total_blank, percent, coins,
          datetime.now().isoformat(), exam_id))
    conn.commit()
    conn.close()


def get_mock_exam(exam_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mock_exams WHERE id = ?", (exam_id,))
    exam = cursor.fetchone()
    conn.close()
    return exam


def get_mock_exam_history(user_id, limit=10):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM mock_exams
        WHERE user_id = ? AND status = 'completed'
        ORDER BY id DESC LIMIT ?
    """, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_mock_exam_count_today(user_id):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as c FROM mock_exams WHERE user_id = ? AND started_at LIKE ?", (user_id, f"{today}%"))
    count = cursor.fetchone()['c']
    conn.close()
    return count


# ============================================================
# خلاصه‌ها
# ============================================================
def save_summary(user_id, title, subject, summary_text):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO summaries (user_id, title, subject, summary_text, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, title, subject, summary_text, datetime.now().isoformat()))
    conn.commit()
    summary_id = cursor.lastrowid
    conn.close()
    return summary_id


def get_summaries(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, subject, created_at FROM summaries WHERE user_id = ? ORDER BY id DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_summary(summary_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM summaries WHERE id = ?", (summary_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def delete_summary(summary_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM summaries WHERE id = ?", (summary_id,))
    conn.commit()
    conn.close()


def get_summaries_count(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as c FROM summaries WHERE user_id = ?", (user_id,))
    count = cursor.fetchone()['c']
    conn.close()
    return count


# ============================================================
# بانک سوالات
# ============================================================
def add_to_question_bank(user_id, subject_id, chapter, grade, field, book,
                          question_text, options, correct_answer, user_answer):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, times_wrong FROM question_bank WHERE user_id = ? AND question_text = ?", (user_id, question_text))
    existing = cursor.fetchone()
    if existing:
        cursor.execute("""
            UPDATE question_bank SET times_wrong = times_wrong + 1, user_answer = ?, added_at = ?
            WHERE id = ?
        """, (user_answer, datetime.now().isoformat(), existing['id']))
    else:
        cursor.execute("""
            INSERT INTO question_bank
            (user_id, subject_id, chapter, grade, field, book,
             question_text, options, correct_answer, user_answer, added_at, times_wrong)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (user_id, subject_id, chapter, grade, field, book,
              question_text, json.dumps(options, ensure_ascii=False),
              correct_answer, user_answer, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_question_bank(user_id, limit=None):
    conn = get_db()
    cursor = conn.cursor()
    if limit:
        cursor.execute("SELECT * FROM question_bank WHERE user_id = ? ORDER BY added_at DESC LIMIT ?", (user_id, limit))
    else:
        cursor.execute("SELECT * FROM question_bank WHERE user_id = ? ORDER BY added_at DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_question_bank_count(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as c FROM question_bank WHERE user_id = ?", (user_id,))
    count = cursor.fetchone()['c']
    conn.close()
    return count


def remove_from_question_bank(question_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM question_bank WHERE id = ?", (question_id,))
    conn.commit()
    conn.close()


def clear_question_bank(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM question_bank WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_question_bank_stats(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as c FROM question_bank WHERE user_id = ?", (user_id,))
    total = cursor.fetchone()['c']
    cursor.execute("""
        SELECT book, chapter, COUNT(*) as c FROM question_bank
        WHERE user_id = ? GROUP BY book, chapter ORDER BY c DESC
    """, (user_id,))
    by_chapter = cursor.fetchall()
    conn.close()
    return {"total": total, "by_chapter": by_chapter}


# ============================================================
# دستاوردها
# ============================================================
def get_user_achievements(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT achievement_id FROM user_achievements WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return {r['achievement_id'] for r in rows}


def grant_achievement(user_id, achievement_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO user_achievements (user_id, achievement_id, earned_at)
        VALUES (?, ?, ?)
    """, (user_id, achievement_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def check_and_grant_achievements(user_id):
    earned = get_user_achievements(user_id)
    newly_earned = []
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as c FROM exams WHERE user_id = ? AND status = 'completed'", (user_id,))
    exam_count = cursor.fetchone()['c']
    cursor.execute("""
        SELECT COUNT(*) as c FROM exams WHERE user_id = ? AND status = 'completed'
        AND score * 100 / 15 >= 100
    """, (user_id,))
    perfect_count = cursor.fetchone()['c']
    cursor.execute("SELECT coins FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    coins = row['coins'] if row else 0
    cursor.execute("SELECT streak FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    streak = row['streak'] if row else 0
    conn.close()
    for ach_id, ach in ACHIEVEMENTS.items():
        if ach_id in earned:
            continue
        value = ach['value']
        ach_type = ach['type']
        should_grant = False
        if ach_type == 'exam_count' and exam_count >= value:
            should_grant = True
        elif ach_type == 'perfect_count' and perfect_count >= value:
            should_grant = True
        elif ach_type == 'coins' and coins >= value:
            should_grant = True
        elif ach_type == 'streak' and streak >= value:
            should_grant = True
        if should_grant:
            grant_achievement(user_id, ach_id)
            add_coins(user_id, COINS_PER_ACHIEVEMENT)
            newly_earned.append(ach)
    return newly_earned


def get_achievements_text(user_id):
    earned = get_user_achievements(user_id)
    categories = {
        "learning": "🎓 یادگیری",
        "consistency": "🔥 استمرار",
        "quality": "🏆 کیفیت",
        "coins": "💰 سکه",
    }
    lines = []
    total = len(ACHIEVEMENTS)
    earned_count = len(earned)
    lines.append(f"🏅 **دستاوردهای تو** ({earned_count}/{total})\n")
    for cat_key, cat_name in categories.items():
        cat_items = {k: v for k, v in ACHIEVEMENTS.items() if v['category'] == cat_key}
        if not cat_items:
            continue
        lines.append(f"\n**{cat_name}**")
        for ach_id, ach in cat_items.items():
            if ach_id in earned:
                lines.append(f"✅ {ach['name']} — {ach['desc']}")
            else:
                lines.append(f"🔒 {ach['name']} — {ach['desc']}")
    return "\n".join(lines)


# ============================================================
# مأموریت‌های روزانه
# ============================================================
def ensure_daily_quests(user_id):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as c FROM user_quests WHERE user_id = ? AND date = ?", (user_id, today))
    count = cursor.fetchone()['c']
    conn.close()
    if count > 0:
        return
    quests = random.sample(DAILY_QUESTS, min(3, len(DAILY_QUESTS)))
    conn = get_db()
    cursor = conn.cursor()
    for q in quests:
        cursor.execute("""
            INSERT OR IGNORE INTO user_quests (user_id, date, quest_id, completed, claimed)
            VALUES (?, ?, ?, 0, 0)
        """, (user_id, today, q['id']))
    conn.commit()
    conn.close()


def get_daily_quests(user_id):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT quest_id, completed, claimed FROM user_quests WHERE user_id = ? AND date = ?", (user_id, today))
    rows = cursor.fetchall()
    conn.close()
    result = []
    for row in rows:
        for q in DAILY_QUESTS:
            if q['id'] == row['quest_id']:
                result.append({**q, "completed": row['completed'], "claimed": row['claimed']})
                break
    return result


def check_quest_completion(user_id):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as c FROM exams WHERE user_id = ? AND status = 'completed' AND completed_at LIKE ?
    """, (user_id, f"{today}%"))
    exams_today = cursor.fetchone()['c']
    cursor.execute("""
        SELECT SUM(duration) as total FROM sessions
        WHERE user_id = ? AND start_time LIKE ? AND status = 'completed'
    """, (user_id, f"{today}%"))
    row = cursor.fetchone()
    minutes_today = row['total'] or 0
    cursor.execute("SELECT quest_id, completed, claimed FROM user_quests WHERE user_id = ? AND date = ?", (user_id, today))
    quests = cursor.fetchall()
    updates = []
    for row in quests:
        quest_id = row['quest_id']
        if row['completed']:
            continue
        quest_info = None
        for q in DAILY_QUESTS:
            if q['id'] == quest_id:
                quest_info = q
                break
        if not quest_info:
            continue
        should_complete = False
        if quest_info['type'] == 'exams_today' and exams_today >= quest_info['value']:
            should_complete = True
        elif quest_info['type'] == 'minutes_today' and minutes_today >= quest_info['value']:
            should_complete = True
        if should_complete:
            cursor.execute("""
                UPDATE user_quests SET completed = 1 WHERE user_id = ? AND date = ? AND quest_id = ?
            """, (user_id, today, quest_id))
            updates.append(quest_info)
    conn.commit()
    conn.close()
    return updates


def claim_quest_reward(user_id, quest_id):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT completed, claimed FROM user_quests WHERE user_id = ? AND date = ? AND quest_id = ?
    """, (user_id, today, quest_id))
    row = cursor.fetchone()
    if not row or not row['completed'] or row['claimed']:
        conn.close()
        return None
    quest_info = None
    for q in DAILY_QUESTS:
        if q['id'] == quest_id:
            quest_info = q
            break
    if not quest_info:
        conn.close()
        return None
    add_coins(user_id, quest_info['coins'])
    add_league_points(user_id, LEAGUE_POINTS["quest_complete"])
    cursor.execute("""
        UPDATE user_quests SET claimed = 1 WHERE user_id = ? AND date = ? AND quest_id = ?
    """, (user_id, today, quest_id))
    conn.commit()
    conn.close()
    return quest_info


def get_daily_quests_text(user_id):
    ensure_daily_quests(user_id)
    quests = get_daily_quests(user_id)
    lines = ["🎯 **مأموریت‌های امروز**\n"]
    has_completed_unclaimed = False
    for q in quests:
        if q['claimed']:
            lines.append(f"✅ {q['text']} — دریافت شد")
        elif q['completed']:
            lines.append(f"🎁 {q['text']} — **آماده‌ی دریافت!** (+{q['coins']} سکه)")
            has_completed_unclaimed = True
        else:
            lines.append(f"⬜ {q['text']} (+{q['coins']} سکه)")
    lines.append("\n💡 مأموریت‌ها هر روز صبح عوض میشن!")
    return "\n".join(lines), has_completed_unclaimed


# ============================================================
# درس‌ها / مطالعه / امتحان
# ============================================================
def get_subjects(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subjects WHERE user_id = ? ORDER BY id DESC", (user_id,))
    subjects = cursor.fetchall()
    conn.close()
    return subjects


def add_subject(user_id, grade, field, book):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO subjects (user_id, grade, field, book, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, grade, field or "", book, datetime.now().isoformat()))
    conn.commit()
    subject_id = cursor.lastrowid
    conn.close()
    return subject_id


def get_subject(subject_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subjects WHERE id = ?", (subject_id,))
    subject = cursor.fetchone()
    conn.close()
    return subject


def start_session(user_id, subject_id, chapter, topics, duration):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sessions (user_id, subject_id, chapter, topics, duration, start_time, status)
        VALUES (?, ?, ?, ?, ?, ?, 'active')
    """, (user_id, subject_id, chapter, topics, duration, datetime.now().isoformat()))
    conn.commit()
    session_id = cursor.lastrowid
    conn.close()
    return session_id


def check_exam_exists(user_id, subject_id, chapter):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM exams WHERE user_id = ? AND subject_id = ? AND chapter = ? AND status = 'completed'
    """, (user_id, subject_id, chapter))
    exam = cursor.fetchone()
    conn.close()
    return exam


def save_exam(user_id, subject_id, chapter, questions, correct_answers):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO exams (user_id, subject_id, chapter, questions, correct_answers, status, started_at)
        VALUES (?, ?, ?, ?, ?, 'active', ?)
    """, (user_id, subject_id, chapter, json.dumps(questions, ensure_ascii=False),
          json.dumps(correct_answers), datetime.now().isoformat()))
    conn.commit()
    exam_id = cursor.lastrowid
    conn.close()
    return exam_id


def complete_exam(exam_id, user_answers, score, coins):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE exams SET user_answers = ?, score = ?, coins_earned = ?, status = 'completed', completed_at = ?
        WHERE id = ?
    """, (json.dumps(user_answers), score, coins, datetime.now().isoformat(), exam_id))
    conn.commit()
    conn.close()


def get_user_stats(user_id):
    conn = get_db()
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT SUM(duration) as total FROM sessions WHERE user_id = ? AND start_time LIKE ?", (user_id, f"{today}%"))
    today_total = cursor.fetchone()['total'] or 0
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    cursor.execute("SELECT SUM(duration) as total FROM sessions WHERE user_id = ? AND start_time >= ?", (user_id, week_ago))
    week_total = cursor.fetchone()['total'] or 0
    cursor.execute("SELECT SUM(duration) as total FROM sessions WHERE user_id = ?", (user_id,))
    all_total = cursor.fetchone()['total'] or 0
    cursor.execute("SELECT COUNT(*) as count FROM sessions WHERE user_id = ?", (user_id,))
    count = cursor.fetchone()['count']
    cursor.execute("SELECT COUNT(*) as count FROM exams WHERE user_id = ? AND status = 'completed'", (user_id,))
    exams_count = cursor.fetchone()['count']
    conn.close()
    return {"today": today_total, "week": week_total, "all": all_total, "count": count, "exams": exams_count}


def get_detailed_stats(user_id):
    conn = get_db()
    cursor = conn.cursor()
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    cursor.execute("SELECT SUM(duration) as total FROM sessions WHERE user_id = ?", (user_id,))
    total_time = cursor.fetchone()['total'] or 0
    cursor.execute("SELECT SUM(duration) as total FROM sessions WHERE user_id = ? AND start_time >= ?", (user_id, week_ago))
    week_time = cursor.fetchone()['total'] or 0
    cursor.execute("""
        SELECT s.book, s.grade, SUM(ss.duration) as total
        FROM sessions ss JOIN subjects s ON ss.subject_id = s.id
        WHERE ss.user_id = ? AND ss.start_time >= ?
        GROUP BY s.book, s.grade ORDER BY total DESC
    """, (user_id, week_ago))
    subjects_week = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) as c FROM sessions WHERE user_id = ?", (user_id,))
    sessions_count = cursor.fetchone()['c']
    cursor.execute("""
        SELECT AVG(CAST(score AS FLOAT) * 100 / 15) as avg_percent
        FROM exams WHERE user_id = ? AND status = 'completed'
    """, (user_id,))
    avg_row = cursor.fetchone()
    avg_percent = avg_row['avg_percent'] if avg_row and avg_row['avg_percent'] else 0
    cursor.execute("SELECT COUNT(*) as c FROM exams WHERE user_id = ? AND status = 'completed'", (user_id,))
    exams_count = cursor.fetchone()['c']
    conn.close()
    subjects_detail = "\n".join([f"  - {r['book']} ({r['grade']}): {r['total']} دقیقه" for r in subjects_week]) or "  - هنوز مطالعه‌ای ثبت نشده"
    return {
        "total_time": total_time, "week_time": week_time,
        "subjects_week": subjects_detail, "sessions_count": sessions_count,
        "avg_percent": avg_percent, "exams_count": exams_count
    }


def get_subjects_pie_data(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.book, SUM(ss.duration) as total
        FROM sessions ss JOIN subjects s ON ss.subject_id = s.id
        WHERE ss.user_id = ? AND ss.status = 'completed'
        GROUP BY s.book ORDER BY total DESC LIMIT 8
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    labels = []
    values = []
    for r in rows:
        labels.append(r['book'])
        values.append(r['total'] or 0)
    return {"labels": labels, "values": values}


def save_plan(user_id, goal, subjects, hours, off_days, plan_text):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO plans (user_id, goal, subjects, hours_per_day, off_days, plan_text, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, goal, subjects, hours, off_days, plan_text, datetime.now().isoformat()))
    conn.commit()
    plan_id = cursor.lastrowid
    conn.close()
    return plan_id


def get_latest_plan(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM plans WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    plan = cursor.fetchone()
    conn.close()
    return plan


def delete_plans(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM plans WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


# ============================================================
# کارنامه تحلیلی
# ============================================================
def get_student_report(user_id, months=3):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.id, e.subject_id, e.chapter, e.score, e.completed_at,
               s.book, s.grade, s.field
        FROM exams e JOIN subjects s ON e.subject_id = s.id
        WHERE e.user_id = ? AND e.status = 'completed'
        ORDER BY e.completed_at ASC
    """, (user_id,))
    exams = cursor.fetchall()
    cursor.execute("""
        SELECT id, percent, total_questions, completed_at FROM mock_exams
        WHERE user_id = ? AND status = 'completed' ORDER BY completed_at ASC
    """, (user_id,))
    mocks = cursor.fetchall()
    conn.close()
    all_scores = []
    chapter_stats = {}
    for e in exams:
        if e['score'] is None:
            continue
        try:
            conn2 = get_db()
            c2 = conn2.cursor()
            c2.execute("SELECT questions FROM exams WHERE id = ?", (e['id'],))
            row = c2.fetchone()
            conn2.close()
            q_count = len(json.loads(row['questions'])) if row and row['questions'] else 15
        except Exception:
            q_count = 15
        percent = (e['score'] / q_count * 100) if q_count > 0 else 0
        label = f"{e['book']} — {e['chapter']}"
        all_scores.append({"percent": percent, "label": label, "date": e['completed_at'], "type": "exam"})
        key = (e['book'], e['chapter'])
        if key not in chapter_stats:
            chapter_stats[key] = {"percents": [], "grade": e['grade'], "field": e['field']}
        chapter_stats[key]["percents"].append(percent)
    for m in mocks:
        if m['percent'] is None:
            continue
        all_scores.append({
            "percent": m['percent'],
            "label": f"🎯 آزمون کنکور ({m['total_questions']} سوال)",
            "date": m['completed_at'], "type": "mock",
        })
    if not all_scores:
        return {"total_count": 0, "avg": 0, "best": None, "worst": None,
                "strengths": [], "weaknesses": [], "chapter_stats": {},
                "timeline": {"labels": [], "values": []}}
    percents = [s['percent'] for s in all_scores]
    avg = sum(percents) / len(percents)
    best_score = max(all_scores, key=lambda x: x['percent'])
    worst_score = min(all_scores, key=lambda x: x['percent'])
    strengths = []
    weaknesses = []
    chapter_avgs = {}
    for (book, chapter), info in chapter_stats.items():
        avg_ch = sum(info['percents']) / len(info['percents'])
        chapter_avgs[(book, chapter)] = avg_ch
        if avg_ch >= 80:
            strengths.append({"book": book, "chapter": chapter, "avg": avg_ch, "count": len(info['percents'])})
        elif avg_ch < 60:
            weaknesses.append({"book": book, "chapter": chapter, "avg": avg_ch, "count": len(info['percents'])})
    strengths.sort(key=lambda x: x['avg'], reverse=True)
    weaknesses.sort(key=lambda x: x['avg'])
    timeline = build_timeline_3months(all_scores, months)
    return {
        "total_count": len(all_scores), "avg": avg,
        "best": best_score, "worst": worst_score,
        "strengths": strengths[:5], "weaknesses": weaknesses[:5],
        "chapter_stats": chapter_avgs, "timeline": timeline,
    }


def build_timeline_3months(all_scores, months=3):
    now = jdatetime.date.today()
    labels = []
    values = []
    
    # لیست اسم ماه‌های شمسی
    month_names = [
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
    ]
    
    for i in range(months - 1, -1, -1):
        # محاسبه ماه هدف به صورت دقیق شمسی
        target_month = now.month - i
        target_year = now.year
        
        while target_month <= 0:
            target_month += 12
            target_year -= 1
            
        start_jdate = jdatetime.date(target_year, target_month, 1)
        
        if target_month == 12:
            end_jdate = jdatetime.date(target_year + 1, 1, 1)
        else:
            end_jdate = jdatetime.date(target_year, target_month + 1, 1)
            
        start_date = start_jdate.togregorian()
        end_date = end_jdate.togregorian()
        
        month_label = month_names[target_month - 1]
        
        month_scores = []
        for s in all_scores:
            if not s['date']:
                continue
            try:
                dt = datetime.fromisoformat(s['date'])
            except Exception:
                continue
            
            # مقایسه درست تاریخ‌ها با تبدیل به datetime
            if datetime.combine(start_date, datetime.min.time()) <= dt < datetime.combine(end_date, datetime.min.time()):
                month_scores.append(s['percent'])
                
        if month_scores:
            avg = sum(month_scores) / len(month_scores)
            values.append(round(avg, 1))
        else:
            values.append(0)
        labels.append(month_label)
        
    return {"labels": labels, "values": values}


def get_user_exams_count(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as c FROM exams WHERE user_id = ? AND status = 'completed'", (user_id,))
    exams_count = cursor.fetchone()['c']
    cursor.execute("SELECT COUNT(*) as c FROM mock_exams WHERE user_id = ? AND status = 'completed'", (user_id,))
    mocks_count = cursor.fetchone()['c']
    conn.close()
    return exams_count + mocks_count


# ============================================================
# پرداخت
# ============================================================
def create_payment_request(user_id, plan_key, duration_key, base_price,
                           discount_percent, coin_used, final_price):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO payment_requests
        (user_id, plan_key, duration_key, base_price, discount_percent,
         coin_used, final_price, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
    """, (user_id, plan_key, duration_key, base_price, discount_percent,
          coin_used, final_price, datetime.now().isoformat()))
    conn.commit()
    request_id = cursor.lastrowid
    conn.close()
    return request_id


def get_payment_request(request_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM payment_requests WHERE id = ?", (request_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def attach_receipt(request_id, file_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE payment_requests SET receipt_file_id = ? WHERE id = ?
    """, (file_id, request_id))
    conn.commit()
    conn.close()


def approve_payment(request_id, admin_id):
    req = get_payment_request(request_id)
    if not req:
        return None
    days = get_plan_days(req['duration_key'])
    set_plan(req['user_id'], req['plan_key'], days)
    reset_coins(req['user_id'])
    mark_user_discounts_used(req['user_id'])
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE payment_requests
        SET status = 'approved', decided_at = ?, decided_by = ?, user_seen = 0
        WHERE id = ?
    """, (datetime.now().isoformat(), admin_id, request_id))
    conn.commit()
    conn.close()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT referred_by, has_purchased FROM users WHERE id = ?", (req['user_id'],))
    user_row = cursor.fetchone()
    was_first_purchase = False
    if user_row and not user_row['has_purchased']:
        cursor.execute("UPDATE users SET has_purchased = 1 WHERE id = ?", (req['user_id'],))
        was_first_purchase = True
        if user_row['referred_by']:
            add_user_discount(user_row['referred_by'], REFERRAL_DISCOUNT_PERCENT, "referral")
            cursor.execute("""
                UPDATE referrals SET first_purchase_at = ?
                WHERE referred_id = ? AND first_purchase_at IS NULL
            """, (datetime.now().isoformat(), req['user_id']))
    conn.commit()
    conn.close()
    return req

def reject_payment(request_id, admin_id, note=""):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE payment_requests
        SET status = 'rejected', admin_note = ?, decided_at = ?, decided_by = ?, user_seen = 0
        WHERE id = ?
    """, (note, datetime.now().isoformat(), admin_id, request_id))
    conn.commit()
    conn.close()

# ============================================================
# دعوت دوستان
# ============================================================
def register_referral(referrer_code, referred_user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE referral_code = ?", (referrer_code,))
    referrer_row = cursor.fetchone()
    if not referrer_row:
        conn.close()
        return False
    referrer_id = referrer_row['id']
    if referrer_id == referred_user_id:
        conn.close()
        return False
    cursor.execute("SELECT referred_by FROM users WHERE id = ?", (referred_user_id,))
    row = cursor.fetchone()
    if row and row['referred_by']:
        conn.close()
        return False
    cursor.execute("UPDATE users SET referred_by = ? WHERE id = ?", (referrer_id, referred_user_id))
    cursor.execute("""
        INSERT OR IGNORE INTO referrals (referrer_id, referred_id, registered_at)
        VALUES (?, ?, ?)
    """, (referrer_id, referred_user_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return True


def get_user_referral_stats(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as c FROM referrals WHERE referrer_id = ?", (user_id,))
    total = cursor.fetchone()['c']
    cursor.execute("""
        SELECT COUNT(*) as c FROM referrals
        WHERE referrer_id = ? AND first_purchase_at IS NOT NULL
    """, (user_id,))
    successful = cursor.fetchone()['c']
    conn.close()
    return {"total": total, "successful": successful}


# ============================================================
# گروه‌های مطالعه
# ============================================================
def generate_group_code():
    conn = get_db()
    cursor = conn.cursor()
    for _ in range(50):
        code = ''.join(random.choices(string.digits, k=GROUP_CODE_LENGTH))
        cursor.execute("SELECT id FROM study_groups WHERE code = ?", (code,))
        if not cursor.fetchone():
            conn.close()
            return code
    conn.close()
    return ''.join(random.choices(string.digits, k=GROUP_CODE_LENGTH))


def create_group(name, owner_id):
    existing = get_user_group(owner_id)
    if existing:
        return None
    code = generate_group_code()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO study_groups (name, code, owner_id, created_at)
        VALUES (?, ?, ?, ?)
    """, (name, code, owner_id, datetime.now().isoformat()))
    group_id = cursor.lastrowid
    cursor.execute("""
        INSERT INTO group_members (group_id, user_id, joined_at)
        VALUES (?, ?, ?)
    """, (group_id, owner_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return group_id, code


def get_group(group_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM study_groups WHERE id = ?", (group_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def get_group_by_code(code):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM study_groups WHERE code = ?", (code,))
    row = cursor.fetchone()
    conn.close()
    return row


def get_user_group(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT sg.* FROM study_groups sg
        JOIN group_members gm ON sg.id = gm.group_id
        WHERE gm.user_id = ?
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def join_group(code, user_id):
    group = get_group_by_code(code)
    if not group:
        return "error", "❌ کد اشتباهه!"
    existing = get_user_group(user_id)
    if existing:
        if existing['id'] == group['id']:
            return "already_member", "تو همین گروه هستی!"
        return "already_in_group", "تو توی یه گروه دیگه‌ای. اول از اون خارج شو."
    members = get_group_members(group['id'])
    if len(members) >= GROUP_MAX_MEMBERS:
        return "full", f"❌ گروه پر شده! ({GROUP_MAX_MEMBERS} نفر)"
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO group_members (group_id, user_id, joined_at)
        VALUES (?, ?, ?)
    """, (group['id'], user_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return "success", group['name']


def leave_group(user_id):
    group = get_user_group(user_id)
    if not group:
        return "not_in_group", None
    if group['owner_id'] == user_id:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM group_challenges WHERE group_id = ?", (group['id'],))
        cursor.execute("DELETE FROM group_members WHERE group_id = ?", (group['id'],))
        cursor.execute("DELETE FROM study_groups WHERE id = ?", (group['id'],))
        conn.commit()
        conn.close()
        return "owner_left", group['name']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM group_members WHERE group_id = ? AND user_id = ?", (group['id'], user_id))
    conn.commit()
    conn.close()
    return "success", group['name']


def get_group_members(group_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.first_name, u.username, u.telegram_id
        FROM group_members gm JOIN users u ON gm.user_id = u.id
        WHERE gm.group_id = ? ORDER BY gm.joined_at ASC
    """, (group_id,))
    rows = cursor.fetchall()
    conn.close()
    result = []
    for r in rows:
        points = get_user_league_points(r['id'])
        study_time = get_user_month_study_time(r['id'])
        result.append({
            "id": r['id'], "first_name": r['first_name'],
            "username": r['username'], "telegram_id": r['telegram_id'],
            "league_points": points, "study_minutes": study_time,
        })
    return result


def get_user_month_study_time(user_id):
    today = jdatetime.date.today()
    month_start = jdatetime.date(today.year, today.month, 1).togregorian()
    month_start_iso = month_start.isoformat()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT SUM(duration) as total FROM sessions
        WHERE user_id = ? AND start_time >= ? AND status = 'completed'
    """, (user_id, month_start_iso))
    row = cursor.fetchone()
    conn.close()
    return row['total'] or 0


def get_group_owner_id(group_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT owner_id FROM study_groups WHERE id = ?", (group_id,))
    row = cursor.fetchone()
    conn.close()
    return row['owner_id'] if row else None


def is_group_owner(group_id, user_id):
    return get_group_owner_id(group_id) == user_id


def create_group_challenge(group_id, challenge_type, goal_value, duration_type, created_by):
    existing = get_group_challenge(group_id)
    if existing:
        return None
    duration = GROUP_CHALLENGE_DURATIONS.get(duration_type)
    if not duration:
        return None
    days = duration['days']
    today = jdatetime.date.today()
    end_date = today + timedelta(days=days)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO group_challenges
        (group_id, challenge_type, goal_value, duration_type,
         start_date, end_date, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (group_id, challenge_type, goal_value, duration_type,
          today.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"),
          created_by, datetime.now().isoformat()))
    conn.commit()
    challenge_id = cursor.lastrowid
    conn.close()
    return challenge_id


def get_group_challenge(group_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM group_challenges WHERE group_id = ?", (group_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def cancel_group_challenge(group_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM group_challenges WHERE group_id = ?", (group_id,))
    conn.commit()
    conn.close()


def get_challenge_progress(group_id):
    challenge = get_group_challenge(group_id)
    if not challenge:
        return None
    challenge_type = challenge['challenge_type']
    goal_value = challenge['goal_value']
    start_date = challenge['start_date']
    members = get_group_members(group_id)
    member_ids = [m['id'] for m in members]
    if not member_ids:
        return {"current": 0, "goal": goal_value, "type": challenge_type, "percent": 0}
    conn = get_db()
    cursor = conn.cursor()
    current = 0
    placeholders = ",".join("?" * len(member_ids))
    if challenge_type == "study_minutes":
        cursor.execute(f"""
            SELECT SUM(duration) as total FROM sessions
            WHERE user_id IN ({placeholders}) AND start_time >= ? AND status = 'completed'
        """, member_ids + [start_date])
        total_minutes = cursor.fetchone()['total'] or 0
        current = total_minutes // 60
    elif challenge_type == "exams_count":
        cursor.execute(f"""
            SELECT COUNT(*) as c FROM exams
            WHERE user_id IN ({placeholders}) AND status = 'completed' AND completed_at >= ?
        """, member_ids + [start_date])
        current = cursor.fetchone()['c']
    elif challenge_type == "mock_exams":
        cursor.execute(f"""
            SELECT COUNT(*) as c FROM mock_exams
            WHERE user_id IN ({placeholders}) AND status = 'completed' AND completed_at >= ?
        """, member_ids + [start_date])
        current = cursor.fetchone()['c']
    elif challenge_type == "stars":
        cursor.execute(f"""
            SELECT COUNT(*) as c FROM user_stars
            WHERE user_id IN ({placeholders}) AND date >= ?
        """, member_ids + [start_date])
        current = cursor.fetchone()['c']
    conn.close()
    percent = min(100, int((current / goal_value) * 100)) if goal_value > 0 else 0
    return {"current": current, "goal": goal_value, "type": challenge_type, "percent": percent}


# ============================================================
# پشتیبانی (جدید)
# ============================================================
def add_support_message(user_id, sender, message_text):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO support_messages (user_id, sender, message_text, is_read, created_at)
        VALUES (?, ?, ?, 0, ?)
    """, (user_id, sender, message_text, datetime.now().isoformat()))
    conn.commit()
    msg_id = cursor.lastrowid
    conn.close()
    return msg_id


def get_support_thread(user_id, limit=50):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM support_messages
        WHERE user_id = ?
        ORDER BY id ASC
        LIMIT ?
    """, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_support_thread_recent(user_id, limit=30):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM (
            SELECT * FROM support_messages
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
        ) ORDER BY id ASC
    """, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_support_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.telegram_id, u.first_name, u.username,
               SUM(CASE WHEN sm.sender = 'user' AND sm.is_read = 0 THEN 1 ELSE 0 END) as unread_count,
               MAX(sm.created_at) as last_message_at
        FROM users u
        JOIN support_messages sm ON u.id = sm.user_id
        GROUP BY u.id
        ORDER BY last_message_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


def mark_support_read(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE support_messages SET is_read = 1
        WHERE user_id = ? AND sender = 'user'
    """, (user_id,))
    conn.commit()
    conn.close()


def mark_admin_messages_read(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE support_messages SET is_read = 1
        WHERE user_id = ? AND sender = 'admin'
    """, (user_id,))
    conn.commit()
    conn.close()


def get_support_unread_count_for_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as c FROM support_messages
        WHERE user_id = ? AND sender = 'admin' AND is_read = 0
    """, (user_id,))
    count = cursor.fetchone()['c']
    conn.close()
    return count


def get_support_unread_count_for_admin():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as c FROM support_messages
        WHERE sender = 'user' AND is_read = 0
    """)
    count = cursor.fetchone()['c']
    conn.close()
    return count

# ============================================================
# توابع ادمین پرداخت (جدید)
# ============================================================
def get_pending_payments():
    """لیست همه‌ی درخواست‌های پرداخت در انتظار تایید"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pr.*, u.first_name, u.telegram_id, u.username
        FROM payment_requests pr
        JOIN users u ON pr.user_id = u.id
        WHERE pr.status = 'pending'
        ORDER BY pr.created_at ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_payments(limit=100):
    """همه‌ی پرداخت‌ها (برای تاریخچه ادمین)"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT pr.*, u.first_name, u.telegram_id, u.username
        FROM payment_requests pr
        JOIN users u ON pr.user_id = u.id
        ORDER BY pr.created_at DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_user_payments(user_id, limit=10):
    """تاریخچه پرداخت‌های یک کاربر"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM payment_requests
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows

# ============================================================
# توابع دیده‌شدن پرداخت (جدید)
# ============================================================
def get_unseen_payment_count(user_id):
    """تعداد پرداخت‌هایی که ادمین تصمیم گرفته ولی کاربر هنوز ندیده"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as c FROM payment_requests
        WHERE user_id = ? AND user_seen = 0
    """, (user_id,))
    count = cursor.fetchone()['c']
    conn.close()
    return count


def mark_payments_seen(user_id):
    """علامت‌گذاری همه‌ی پرداخت‌های دیده‌نشده کاربر به عنوان دیده‌شده"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE payment_requests SET user_seen = 1
        WHERE user_id = ? AND user_seen = 0
    """, (user_id,))
    conn.commit()
    conn.close()

# ============================================================
# توابع دیده‌شدن پرداخت
# ============================================================
def get_unseen_payment_count(user_id):
    """تعداد پرداخت‌هایی که ادمین تصمیم گرفته ولی کاربر هنوز ندیده"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) as c FROM payment_requests
        WHERE user_id = ? AND user_seen = 0
    """, (user_id,))
    count = cursor.fetchone()['c']
    conn.close()
    return count


def mark_payments_seen(user_id):
    """علامت‌گذاری همه‌ی پرداخت‌های دیده‌نشده کاربر به عنوان دیده‌شده"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE payment_requests SET user_seen = 1
        WHERE user_id = ? AND user_seen = 0
    """, (user_id,))
    conn.commit()
    conn.close()


# ============================================================
# توابع تاریخچه چت هوش مصنوعی
# ============================================================
def get_ai_chat_history(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT role, message_text FROM ai_chat_history WHERE user_id = ? ORDER BY id ASC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r["role"], "text": r["message_text"]} for r in rows]

def save_ai_chat_message(user_id, role, text):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ai_chat_history (user_id, role, message_text, created_at) VALUES (?, ?, ?, ?)", (user_id, role, text, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def clear_ai_chat_history(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ai_chat_history WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# ============================================================
# توابع تاریخچه برنامه‌ریزی (جدول جدید user_plans)
# ============================================================
def get_user_plans(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_plans WHERE user_id = ? ORDER BY id DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def save_user_plan(user_id, goal, subjects, hours, off_days, plan_text):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_plans (user_id, goal, subjects, hours, off_days, plan_text, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, goal, subjects, hours, off_days, plan_text, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def delete_user_plan(user_id, plan_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_plans WHERE id = ? AND user_id = ?", (plan_id, user_id))
    conn.commit()
    conn.close()

print("✅ bot_2.py (دیتابیس) لود شد")
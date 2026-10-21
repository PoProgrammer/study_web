"""
فایل تنظیمات StudyBot
همه‌ی اعداد، قیمت‌ها، جایزه‌ها اینجان
برای تغییر هر چیزی فقط این فایل رو ویرایش کن
"""

# ============================================================
# سکه‌ها و جایزه‌ها
# ============================================================

COINS_EXAM_50_TO_70 = 3
COINS_EXAM_70_TO_90 = 5
COINS_EXAM_90_TO_100 = 10
COINS_EXAM_BELOW_50 = 0

COINS_PER_ACHIEVEMENT = 5

COINS_DAILY_QUEST = 10

COINS_STREAK_3_DAYS = 5
COINS_STREAK_7_DAYS = 15
COINS_STREAK_30_DAYS = 50

COINS_BATTLE_WIN = 10
COINS_BATTLE_LOSS = -5

COINS_LEAGUE_RANK_1 = 100
COINS_LEAGUE_RANK_2 = 50
COINS_LEAGUE_RANK_3 = 25

# ============================================================
# پلن‌های اشتراک
# ============================================================

PLANS = {
    "free": {
        "name": "رایگان",
        "emoji": "🆓",
        "price": 0,
        "days": 0,
        "exams_per_day": 2,
        "ai_per_day": 1,
        "questions_per_exam": 10,
        "plan_feature": False,
        "advanced_chart": False,
    },
    "bronze": {
        "name": "برنزی",
        "emoji": "🥉",
        "price": 50,
        "days": 7,
        "exams_per_day": 5,
        "ai_per_day": 5,
        "questions_per_exam": 15,
        "plan_feature": True,
        "advanced_chart": False,
    },
    "silver": {
        "name": "نقره‌ای",
        "emoji": "🥈",
        "price": 100,
        "days": 30,
        "exams_per_day": 10,
        "ai_per_day": 15,
        "questions_per_exam": 20,
        "plan_feature": True,
        "advanced_chart": True,
    },
    "gold": {
        "name": "طلایی",
        "emoji": "🥇",
        "price": 300,
        "days": 90,
        "exams_per_day": 999,
        "ai_per_day": 999,
        "questions_per_exam": 25,
        "plan_feature": True,
        "advanced_chart": True,
    },
}

# ============================================================
# دستاوردها
# ============================================================

ACHIEVEMENTS = {
    # یادگیری
    "first_exam": {
        "name": "🌱 شروع‌کننده",
        "desc": "اولین امتحان",
        "type": "exam_count",
        "value": 1,
        "category": "learning",
    },
    "ten_exams": {
        "name": "📚 کتاب‌خوان",
        "desc": "۱۰ امتحان",
        "type": "exam_count",
        "value": 10,
        "category": "learning",
    },
    "fifty_exams": {
        "name": "🎓 دانش‌آموز",
        "desc": "۵۰ امتحان",
        "type": "exam_count",
        "value": 50,
        "category": "learning",
    },
    "hundred_exams": {
        "name": "🏛️ فیلسوف",
        "desc": "۱۰۰ امتحان",
        "type": "exam_count",
        "value": 100,
        "category": "learning",
    },
    # استمرار
    "streak_3": {
        "name": "🔥 ۳ روز متوالی",
        "desc": "۳ روز پشت سر هم مطالعه",
        "type": "streak",
        "value": 3,
        "category": "consistency",
    },
    "streak_7": {
        "name": "🔥🔥 ۷ روز متوالی",
        "desc": "۷ روز پشت سر هم مطالعه",
        "type": "streak",
        "value": 7,
        "category": "consistency",
    },
    "streak_30": {
        "name": "🔥🔥🔥 ۳۰ روز متوالی",
        "desc": "۳۰ روز پشت سر هم مطالعه",
        "type": "streak",
        "value": 30,
        "category": "consistency",
    },
    # کیفیت
    "perfect_1": {
        "name": "⭐ نمره‌ی کامل",
        "desc": "اولین نمره‌ی ۱۰۰٪",
        "type": "perfect_count",
        "value": 1,
        "category": "quality",
    },
    "perfect_5": {
        "name": "🌟 ۵ بار نمره‌ی کامل",
        "desc": "۵ بار نمره‌ی ۱۰۰٪",
        "type": "perfect_count",
        "value": 5,
        "category": "quality",
    },
    "perfect_10": {
        "name": "💫 ۱۰ بار نمره‌ی کامل",
        "desc": "۱۰ بار نمره‌ی ۱۰۰٪",
        "type": "perfect_count",
        "value": 10,
        "category": "quality",
    },
    # سکه
    "coins_100": {
        "name": "💰 ۱۰۰ سکه",
        "desc": "به ۱۰۰ سکه رسیدی",
        "type": "coins",
        "value": 100,
        "category": "coins",
    },
    "coins_500": {
        "name": "💎 ۵۰۰ سکه",
        "desc": "به ۵۰۰ سکه رسیدی",
        "type": "coins",
        "value": 500,
        "category": "coins",
    },
}

# ============================================================
# مأموریت روزانه (فاز بعد)
# ============================================================

DAILY_QUESTS = [
    {"id": "exam_1", "text": "۱ امتحان بده", "type": "exams_today", "value": 1, "coins": 5},
    {"id": "exam_3", "text": "۳ امتحان بده", "type": "exams_today", "value": 3, "coins": 15},
    {"id": "study_30", "text": "۳۰ دقیقه مطالعه کن", "type": "minutes_today", "value": 30, "coins": 5},
    {"id": "study_60", "text": "۱ ساعت مطالعه کن", "type": "minutes_today", "value": 60, "coins": 10},
    {"id": "study_120", "text": "۲ ساعت مطالعه کن", "type": "minutes_today", "value": 120, "coins": 20},
]

# ============================================================
# مرور فاصله‌دار (فاز بعد)
# ============================================================

SPACED_REPETITION_INTERVALS = [3, 7, 14, 30, 60, 90]
REVIEW_QUESTIONS_COUNT = 10

# ============================================================
# تخم مرغ شانس (فاز بعد)
# ============================================================

EGG_DROP_CHANCE = 0.1
EGG_TYPES = {
    "common": {"name": "🥚 معمولی", "chance": 0.6},
    "rare": {"name": "🐣 کمیاب", "chance": 0.3},
    "epic": {"name": "🦅 افسانه‌ای", "chance": 0.1},
}

# ============================================================
# تنظیمات کلی
# ============================================================

MAX_TEXT_LENGTH = 4000
MIN_MINUTES_FOR_STREAK = 10
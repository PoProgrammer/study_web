import json
import re
import urllib.parse
import time
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot_1 import (
    client,
    GRADES_WITH_FIELD,
    LEAGUE_GRADES,
    GROUP_MAX_MEMBERS,
    GROUP_CHALLENGE_TYPES,
    GROUP_CHALLENGE_DURATIONS,
    STAR_REWARDS,
    KONKUR_EXAM_STRUCTURE,
    KONKUR_COEFFICIENTS,
    KONKUR_MAJORS,
    PLAN_PRICES_TOMAN,
    COIN_TO_TOMAN,
    COIN_DISCOUNT_PERCENT,
    REFERRAL_DISCOUNT_PERCENT,
    REFERRED_DISCOUNT_PERCENT,
)

from bot_2 import (
    get_db, get_user_league_points, get_user_league_rank,
    get_question_bank_stats, get_detailed_stats, get_subjects,
    get_student_report, get_user_exams_count,
    get_mock_exam_history,
    get_user_stars, get_claimed_star_rewards, get_next_star_milestone,
    get_jalali_month_display, get_days_until_month_end,
    get_user_group, get_group_members, get_group_challenge,
    get_challenge_progress, is_group_owner,
    get_plan_price_toman, get_user_discounts, get_total_referral_discount,
    calculate_purchase, get_user_referral_stats,
    get_jalali_month_key,
)


def has_field(grade_text):
    g = grade_text.strip()
    return any(g == x or g == f"پایه {x}" or g == f"پایه‌ی {x}" for x in GRADES_WITH_FIELD)


def generate_battle_code():
    import random
    import string
    return ''.join(random.choices(string.digits, k=6))


def format_toman(amount):
    return f"{amount:,}"


def generate_chart_url(user_id, days=7):
    conn = get_db()
    cursor = conn.cursor()
    labels = []
    values = []
    for i in range(days - 1, -1, -1):
        day = datetime.now() - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        day_label = day.strftime("%m/%d")
        cursor.execute("""
            SELECT SUM(duration) as total FROM sessions
            WHERE user_id = ? AND start_time LIKE ?
        """, (user_id, f"{day_str}%"))
        total = cursor.fetchone()['total'] or 0
        labels.append(day_label)
        values.append(total)
    conn.close()
    chart_config = {
        "type": "bar",
        "data": {
            "labels": labels,
            "datasets": [{
                "label": "دقیقه مطالعه",
                "data": values,
                "backgroundColor": "rgba(54, 162, 235, 0.7)",
                "borderColor": "rgba(54, 162, 235, 1)",
                "borderWidth": 2
            }]
        },
        "options": {
            "title": {"display": True, "text": f"📊 مطالعه {days} روز اخیر", "fontSize": 18},
            "scales": {"y": {"beginAtZero": True, "title": {"display": True, "text": "دقیقه"}}},
            "plugins": {"legend": {"display": False}}
        }
    }
    chart_json = json.dumps(chart_config, ensure_ascii=False)
    encoded = urllib.parse.quote(chart_json)
    return f"https://quickchart.io/chart?c={encoded}&w=600&h=400&bkg=white"


def generate_report_chart_url(labels, values):
    chart_config = {
        "type": "line",
        "data": {
            "labels": labels,
            "datasets": [{
                "label": "میانگین درصد",
                "data": values,
                "borderColor": "rgba(75, 192, 192, 1)",
                "backgroundColor": "rgba(75, 192, 192, 0.2)",
                "borderWidth": 3,
                "fill": True,
                "tension": 0.3,
                "pointRadius": 6,
                "pointBackgroundColor": "rgba(75, 192, 192, 1)",
            }]
        },
        "options": {
            "title": {"display": True, "text": "📈 پیشرفت ۳ ماه اخیر", "fontSize": 18},
            "scales": {
                "y": {"beginAtZero": True, "max": 100, "title": {"display": True, "text": "درصد"}}
            },
            "plugins": {"legend": {"display": False}}
        }
    }
    chart_json = json.dumps(chart_config, ensure_ascii=False)
    encoded = urllib.parse.quote(chart_json)
    return f"https://quickchart.io/chart?c={encoded}&w=700&h=400&bkg=white"


def generate_pie_chart_url(labels, values):
    colors = [
        "rgba(255, 99, 132, 0.8)",
        "rgba(54, 162, 235, 0.8)",
        "rgba(255, 206, 86, 0.8)",
        "rgba(75, 192, 192, 0.8)",
        "rgba(153, 102, 255, 0.8)",
        "rgba(255, 159, 64, 0.8)",
        "rgba(199, 199, 199, 0.8)",
        "rgba(83, 102, 255, 0.8)",
    ]
    chart_config = {
        "type": "doughnut",
        "data": {
            "labels": labels,
            "datasets": [{
                "data": values,
                "backgroundColor": colors[:len(labels)],
                "borderWidth": 2,
                "borderColor": "#fff",
            }]
        },
        "options": {
            "title": {"display": True, "text": "📊 سهم دروس در مطالعه", "fontSize": 18},
            "plugins": {"legend": {"display": True, "position": "bottom"}}
        }
    }
    chart_json = json.dumps(chart_config, ensure_ascii=False)
    encoded = urllib.parse.quote(chart_json)
    return f"https://quickchart.io/chart?c={encoded}&w=700&h=500&bkg=white"


def calculate_konkur_rank(user_id, field):
    mocks = get_mock_exam_history(user_id, limit=1)
    if not mocks:
        return None
    latest = mocks[0]
    percent = latest['percent'] or 0
    taraz = 4000 + (percent / 100) * 8000
    if taraz >= 11500:
        rank = int(50 * (12000 - taraz) / 500)
    elif taraz >= 11000:
        rank = int(300 * (12000 - taraz) / 1000)
    elif taraz >= 10000:
        rank = int(1000 * (12000 - taraz) / 2000)
    elif taraz >= 9000:
        rank = int(3000 * (12000 - taraz) / 3000)
    elif taraz >= 8000:
        rank = int(10000 * (12000 - taraz) / 4000)
    else:
        rank = int(30000 * (12000 - taraz) / 4000)
    rank = max(1, rank)
    majors = KONKUR_MAJORS.get(field, [])
    results = []
    for m in majors:
        major_rank = m['rank']
        if rank <= major_rank:
            chance = 90
        elif rank <= major_rank * 1.2:
            chance = 70
        elif rank <= major_rank * 1.5:
            chance = 50
        elif rank <= major_rank * 2:
            chance = 30
        elif rank <= major_rank * 3:
            chance = 15
        else:
            chance = 5
        results.append({"name": m['name'], "chance": chance, "region": m.get('region', 1)})
    return {"percent": percent, "taraz": int(taraz), "rank": rank, "majors": results}


def format_konkur_prediction(field, result):
    if not result:
        return None
    rank = result['rank']
    percent = result['percent']
    lines = [
        f"🎓 **پیش‌بینی رتبه کنکور**\n",
        f"📚 رشته: {field}",
        f"📊 آخرین آزمون: {percent:.1f}%\n",
        f"━━━━━━━━━━━━━━━\n",
        f"🎯 **رتبه تقریبی: {rank:,}**\n",
        f"📈 **درصد قبولی رشته‌ها:**\n",
    ]
    for m in result['majors']:
        chance = m['chance']
        if chance >= 70:
            emoji = "🟢"
        elif chance >= 40:
            emoji = "🟡"
        else:
            emoji = "🔴"
        lines.append(f"{emoji} {m['name']}: **{chance}%**")
    return "\n".join(lines)


def format_group_challenge(challenge, progress, user_id, is_owner):
    if not challenge:
        return "❌ چالش فعالی نیست"
    c_type = challenge['challenge_type']
    c_type_info = GROUP_CHALLENGE_TYPES.get(c_type, {})
    type_name = c_type_info.get('name', c_type)
    unit = c_type_info.get('unit', '')
    duration_type = challenge['duration_type']
    duration_info = GROUP_CHALLENGE_DURATIONS.get(duration_type, {})
    duration_name = duration_info.get('name', duration_type)
    end_date = challenge['end_date']
    lines = [
        f"🎯 **چالش فعال گروه:**\n\n",
        f"📌 {type_name}\n",
        f"🎯 هدف: **{challenge['goal_value']}** {unit}\n",
        f"⏰ {duration_name}\n",
        f"📅 پایان: {end_date}\n\n",
    ]
    if progress:
        current = progress['current']
        goal = progress['goal']
        percent = progress['percent']
        filled = int(percent / 100 * 10)
        bar = "█" * filled + "░" * (10 - filled)
        lines.append(f"📊 پیشرفت: **{current}/{goal}** {unit}\n")
        lines.append(f"{bar} {percent}%\n")
        if percent >= 100:
            lines.append(f"\n✅ **چالش کامل شد!** 🎉")
    return "".join(lines)


def format_group_view(group, members, user_id):
    is_owner = is_group_owner(group['id'], user_id)
    sorted_members = sorted(members, key=lambda m: m['league_points'], reverse=True)
    lines = [
        f"👥 **گروه «{group['name']}»**\n\n",
        f"📝 کد: `{group['code']}`\n",
        f"👥 اعضا: {len(members)}/{GROUP_MAX_MEMBERS}\n\n",
        f"━━━━━━━━━━━━━━━\n\n",
        f"🏆 **لیدربورد گروه:**\n\n",
    ]
    for i, m in enumerate(sorted_members[:10], 1):
        if i == 1:
            medal = "🥇"
        elif i == 2:
            medal = "🥈"
        elif i == 3:
            medal = "🥉"
        else:
            medal = f"{i}."
        is_me = " ⭐" if m['id'] == user_id else ""
        owner_mark = " 👑" if m['id'] == group['owner_id'] else ""
        hours = m['study_minutes'] // 60
        minutes = m['study_minutes'] % 60
        if hours > 0:
            study_str = f"{hours}s {minutes}د"
        else:
            study_str = f"{minutes}د"
        lines.append(f"{medal} {m['first_name']}{owner_mark} — **{m['league_points']}** امتیاز")
        lines.append(f"    📚 {study_str} این ماه\n")
    total_points = sum(m['league_points'] for m in members)
    total_minutes = sum(m['study_minutes'] for m in members)
    total_hours = total_minutes // 60
    lines.append(f"━━━━━━━━━━━━━━━\n\n")
    lines.append(f"📊 **آمار گروه:**\n")
    lines.append(f"• مجموع امتیاز: **{total_points}**\n")
    lines.append(f"• مجموع مطالعه: **{total_hours}** ساعت\n")
    return "\n".join(lines)


# ============================================================
# Groq
# ============================================================
def generate_exam_questions(grade, field, book, chapter, topics, count=15):
    field_line = f"- رشته: {field}\n" if field else ""
    prompt = f"""تو یه معلم حرفه‌ای کتاب درسی ایران هستی.

اطلاعات:
- پایه: {grade}
{field_line}- کتاب: {book}
- فصل: {chapter}
- مباحث این فصل: {topics}

از همین مباحث یه امتحان چهارگزینه‌ای با {count} سوال بساز.

قواعد:
- فقط و فقط از مباحث بالا سوال بساز.
- ۴ گزینه برای هر سوال.
- پاسخ صحیح: شماره گزینه از ۰ تا ۳.
- سوالات فارسی و روان.

فرمت خروجی (فقط JSON):
[
  {{
    "q": "متن سوال",
    "options": ["گزینه ۱", "گزینه ۲", "گزینه ۳", "گزینه ۴"],
    "answer": 0
  }}
]

حالا دقیقاً {count} سوال بساز:
"""
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "تو یه معلم دقیق ایرانی هستی. فقط JSON برمی‌گردونی."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4, max_tokens=5000, timeout=120.0
        )
        content = response.choices[0].message.content
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return None
    except Exception as e:
        print(f"❌ خطا Groq: {e}")
        return None


def generate_battle_questions(subject, grade, field, count=7):
    field_line = f"- رشته: {field}\n" if field else ""
    prompt = f"""تو یه معلم {subject} پایه {grade} هستی.

{field_line}از کتاب «{subject}» یه امتحان سریع چهارگزینه‌ای با {count} سوال بساز.

قواعد:
- سوالات متوسط.
- ۴ گزینه.
- پاسخ صحیح: ۰ تا ۳.
- فارسی روان.

فرمت خروجی (فقط JSON):
[
  {{
    "q": "سوال",
    "options": ["الف", "ب", "ج", "د"],
    "answer": 0
  }}
]
"""
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "فقط JSON برگردون."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5, max_tokens=3000, timeout=120.0
        )
        content = response.choices[0].message.content
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return None
    except Exception as e:
        print(f"❌ خطا نبرد: {e}")
        return None


def generate_konkur_questions(field, subjects_list):
    all_questions = []
    CHUNK_SIZE = 20
    
    for subject in subjects_list:
        subject_name = subject["name"]
        total_count = subject["count"]
        
        subject_questions = []
        remaining = total_count
        
        while remaining > 0:
            current_chunk = min(CHUNK_SIZE, remaining)
            
            # 💡 اینجا ۵ سوال بیشتر از نیاز می‌سازیم که کم نیاد
            ask_count = current_chunk + 5
            
            print(f"⏳ در حال ساخت {current_chunk} سوال برای {subject_name} (باقی‌مانده: {remaining})...")
            
            prompt = f"""تو یه طراح سوال کنکور سراسری ایران هستی.

رشته: {field}
درس: {subject_name}

دقیقاً {ask_count} سوال چهارگزینه‌ای در **سطح دشواری کنکور سراسری ایران** بساز.
سوالات باید:
- ۴ گزینه داشته باشن
- پاسخ صحیح: ۰ تا ۳
- فارسی روان

فرمت خروجی (فقط JSON):
{{
  "questions": [
    {{
      "subject": "{subject_name}",
      "q": "متن سوال",
      "options": ["گزینه ۱", "گزینه ۲", "گزینه ۳", "گزینه ۴"],
      "answer": 0
    }}
  ]
}}

فقط JSON برگردون."""
            
            try:
                response = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[
                        {"role": "system", "content": "تو یه طراح سوال کنکور ایران هستی. فقط JSON برمی‌گردونی."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5, max_tokens=6000, timeout=120.0
                )
                content = response.choices[0].message.content
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    cleaned_json = json_match.group().replace('\\', '\\\\')
                    data = json.loads(cleaned_json)
                    chunk_qs = data.get("questions", [])
                    subject_questions.extend(chunk_qs)
                
                remaining -= current_chunk
            except Exception as e:
                print(f"❌ خطا در تکه {subject_name}: {e}")
                time.sleep(2)
                continue
        
        exact_questions = subject_questions[:total_count]
        all_questions.extend(exact_questions)
        print(f"✅ درس {subject_name}: {len(exact_questions)} سوال اضافه شد.")
    
    if not all_questions:
        print("❌ هیچ سوالی استخراج نشد.")
        return None

    print(f"✅ مجموع {len(all_questions)} سوال آماده شد.")
    return all_questions


def generate_summary(text, title, subject):
    subject_line = f"درس: {subject}\n" if subject else ""
    prompt = f"""تو یه معلم حرفه‌ای هستی که متن‌های درسی رو خلاصه می‌کنی.

عنوان: {title}
{subject_line}
متن:
{text}

خلاصه‌ی مرتب با این ساختار:
📌 تعریف‌های کلیدی
🔑 نکات مهم
📐 فرمول‌ها
💡 نکات کاربردی
📚 خلاصه‌ی نهایی

فارسی روان."""
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "تو یه خلاصه‌ساز دقیق هستی. فارسی."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5, max_tokens=2500, timeout=120.0
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ خطا خلاصه: {e}")
        return None


def ask_advisor(user, question):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT SUM(duration) FROM sessions WHERE user_id = ? AND status = 'completed'", (user['id'],))
    total_time = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(duration) FROM sessions WHERE user_id = ? AND status = 'completed' AND start_time >= date('now', '-7 days')", (user['id'],))
    week_time = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT book, grade FROM subjects WHERE user_id = ?", (user['id'],))
    subjects = cursor.fetchall()
    subjects_text = "\n".join([f"- {s[0]} ({s[1]})" for s in subjects]) or "هیچ درسی ثبت نکردی"
    
    cursor.execute("SELECT COUNT(*) FROM exams WHERE user_id = ? AND status = 'completed'", (user['id'],))
    exam_count = cursor.fetchone()[0] or 0
    cursor.execute("SELECT AVG(CAST(score AS FLOAT) * 100 / 15) FROM exams WHERE user_id = ? AND status = 'completed'", (user['id'],))
    avg_score = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT percent, completed_at FROM mock_exams WHERE user_id = ? AND status = 'completed' ORDER BY id DESC LIMIT 1", (user['id'],))
    last_mock = cursor.fetchone()
    mock_text = f"{last_mock[0]:.1f}% (تاریخ: {last_mock[1][:10]})" if last_mock else "هنوز آزمون کنکور ندادی"
    
    cursor.execute("SELECT COUNT(*) FROM question_bank WHERE user_id = ?", (user['id'],))
    wrong_qs = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT coins FROM users WHERE id = ?", (user['id'],))
    coins = cursor.fetchone()[0] or 0
    cursor.execute("SELECT points FROM league_points WHERE user_id = ? AND month_key = ?", (user['id'], get_jalali_month_key()))
    league_pts = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT plan, plan_expires_at FROM users WHERE id = ?", (user['id'],))
    plan_row = cursor.fetchone()
    plan_text = f"{plan_row[0]} (تا {plan_row[1][:10]})" if plan_row[0] != 'free' else "رایگان"
    
    conn.close()
    
    system_prompt = f"""تو یه مشاور تحصیلی حرفه‌ای و دقیق هستی.
وظیفه تو اینه که بر اساس **واقعیت‌های زیر** به کاربر مشاوره بدی. از خودت چیزی نساز و فقط بر اساس اطلاعات زیر جواب بده.

📊 **اطلاعات دقیق کاربر:**
- نام: {user['first_name']}
- پایه: {user['grade']} | رشته: {user['field']}
- پلن: {plan_text}
- سکه: {coins} | امتیاز لیگ: {league_pts}

📚 **درس‌های ثبت‌شده:**
{subjects_text}

⏱ **آمار مطالعه:**
- کل مطالعه: {total_time} دقیقه
- مطالعه ۷ روز اخیر: {week_time} دقیقه

📝 **وضعیت امتحان‌ها:**
- تعداد امتحان: {exam_count}
- میانگین نمرات: {avg_score:.1f}%
- آخرین آزمون کنکور: {mock_text}
- تعداد سوالات غلط (بانک سوالات): {wrong_qs}

⚠️ **قوانین پاسخگویی:**
1. اگر اطلاعاتی وجود ندارد (مثلاً هنوز امتحانی نداده)، کاربر را تشویق کن که آن کار را انجام دهد.
2. تحلیلت باید بر اساس اعداد بالا باشد (مثلاً: چون میانگینت ۴۰٪ است، باید روی درس‌های ضعیف تمرکز کنی).
3. پاسخ کوتاه، انگیزه‌بخش و در حداکثر ۱۰ خط باشد.
4. پاسخ را به فارسی روان بنویس."""
    
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.7, max_tokens=1500, timeout=120.0
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ خطا مشاور: {e}")
        return None


def ask_ai_analysis(user, report):
    strengths_text = "\n".join(
        [f"✅ {s['book']} — {s['chapter']}: {s['avg']:.1f}% ({s['count']} امتحان)" for s in report['strengths']]
    ) or "هیچی"
    weaknesses_text = "\n".join(
        [f"❌ {w['book']} — {w['chapter']}: {w['avg']:.1f}% ({w['count']} امتحان)" for w in report['weaknesses']]
    ) or "هیچی"
    grade = user['grade'] if user['grade'] else "نامشخص"
    prompt = f"""تو یه مشاور تحصیلی حرفه‌ای ایران هستی.

اطلاعات:
- پایه: {grade}
- امتحان‌ها: {report['total_count']}
- میانگین: {report['avg']:.1f}%
- بهترین: {report['best']['label']} → {report['best']['percent']:.1f}%
- ضعیف‌ترین: {report['worst']['label']} → {report['worst']['percent']:.1f}%

نقاط قوت:
{strengths_text}

نقاط ضعف:
{weaknesses_text}

تحلیل فارسی روان بده:
📊 **الگوها:** (۲-۳ الگو)
🎯 **پیشنهاد عملی:** (۳ پیشنهاد)
💪 **انگیزه:** (یه جمله)

حداکثر ۱۲ خط."""
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "تو یه مشاور تحصیلی ایران هستی. فارسی روان."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7, max_tokens=1500, timeout=120.0
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ خطا تحلیل AI: {e}")
        return None


def generate_weekly_plan(goal, subjects, hours_per_day, off_days):
    prompt = f"""تو یه برنامه‌ریز تحصیلی هستی.

هدف: {goal}
درس‌ها: {subjects}
ساعت روزانه: {hours_per_day}
تعطیلات: {off_days}

برنامه هفتگی (شنبه تا جمعه). فارسی و مرتب."""
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "تو یه برنامه‌ریز منظم هستی. فارسی."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6, max_tokens=3000, timeout=120.0
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ خطا برنامه: {e}")
        return None


# ============================================================
# منوها
# ============================================================
def get_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 درس‌ها", callback_data="menu_subjects"),
         InlineKeyboardButton("⏱️ شروع مطالعه", callback_data="menu_start_study")],
        [InlineKeyboardButton("💰 سکه‌ها", callback_data="menu_coins"),
         InlineKeyboardButton("🌟 ستاره‌ها", callback_data="menu_stars")],
        [InlineKeyboardButton("📊 آمار من", callback_data="menu_stats"),
         InlineKeyboardButton("📊 کارنامه من", callback_data="menu_report")],
        [InlineKeyboardButton("🎯 آزمون کنکور", callback_data="menu_mock"),
         InlineKeyboardButton("🎓 پیش‌بینی رتبه", callback_data="menu_konkur")],
        [InlineKeyboardButton("⚔️ نبرد ۱ به ۱", callback_data="menu_battle"),
         InlineKeyboardButton("🏆 لیگ ماهانه", callback_data="menu_league")],
        [InlineKeyboardButton("👥 گروه مطالعه", callback_data="menu_groups"),
         InlineKeyboardButton("🎯 مأموریت‌ها", callback_data="menu_quests")],
        [InlineKeyboardButton("🏅 دستاوردها", callback_data="menu_achievements"),
         InlineKeyboardButton("📚 بانک سوالات", callback_data="menu_qbank")],
        [InlineKeyboardButton("📝 خلاصه‌ساز", callback_data="menu_summary"),
         InlineKeyboardButton("🤖 مشاور هوشمند", callback_data="menu_ai")],
        [InlineKeyboardButton("📅 برنامه‌ریزی", callback_data="menu_plan"),
         InlineKeyboardButton("🎁 دعوت دوستان", callback_data="menu_referral")],
        [InlineKeyboardButton("💎 اشتراک", callback_data="menu_subscription"),
         InlineKeyboardButton("📞 پشتیبانی", callback_data="menu_support")],
    ])


def get_league_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 لیدربورد", callback_data="league_leaderboard")],
        [InlineKeyboardButton("📖 جایزه‌ها", callback_data="league_prizes")],
        [InlineKeyboardButton("🏅 بردهای من", callback_data="league_history")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")],
    ])


def get_battle_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 ساخت نبرد جدید", callback_data="battle_create")],
        [InlineKeyboardButton("🔗 پیوستن به نبرد", callback_data="battle_join")],
        [InlineKeyboardButton("📖 تاریخچه‌ی نبردها", callback_data="battle_history")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")],
    ])


def get_battle_subject_menu(user_id):
    subjects = get_subjects(user_id)
    keyboard = []
    for s in subjects:
        if s['field']:
            label = f"📖 {s['book']} — {s['grade']} {s['field']}"
        else:
            label = f"📖 {s['book']} — {s['grade']}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"battle_subj_{s['id']}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="menu_battle")])
    return InlineKeyboardMarkup(keyboard)


def get_mock_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ آزمون جدید", callback_data="mock_new")],
        [InlineKeyboardButton("📖 تاریخچه", callback_data="mock_history")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")],
    ])


def get_mock_start_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 شروع آزمون", callback_data="mock_start_confirm")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="menu_mock")],
    ])


def get_summary_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ خلاصه‌ی جدید", callback_data="summary_new")],
        [InlineKeyboardButton("📖 خلاصه‌های من", callback_data="summary_list")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")],
    ])


def get_qbank_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 امتحان از سوالات اشتباه", callback_data="qbank_exam")],
        [InlineKeyboardButton("📖 دیدن سوالات", callback_data="qbank_view")],
        [InlineKeyboardButton("🗑️ پاک کردن بانک", callback_data="qbank_clear")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")],
    ])


def get_back_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]])


def get_plan_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ ساخت برنامه", callback_data="plan_new")],
        [InlineKeyboardButton("📖 دیدن برنامه", callback_data="plan_view")],
        [InlineKeyboardButton("🗑️ حذف", callback_data="plan_delete")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")],
    ])


def get_report_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📈 نمودار ۳ ماه", callback_data="report_chart")],
        [InlineKeyboardButton("🤖 تحلیل هوشمند", callback_data="report_ai")],
        [InlineKeyboardButton("🔄 بروزرسانی", callback_data="menu_report")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")],
    ])


def get_konkur_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 بروزرسانی", callback_data="menu_konkur")],
        [InlineKeyboardButton("🎯 آزمون جدید", callback_data="menu_mock")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")],
    ])


def get_field_select_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📚 ریاضی", callback_data="set_field_ریاضی")],
        [InlineKeyboardButton("📚 تجربی", callback_data="set_field_تجربی")],
        [InlineKeyboardButton("📚 انسانی", callback_data="set_field_انسانی")],
    ])


def get_stars_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 بروزرسانی", callback_data="menu_stars")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")],
    ])


def get_groups_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ ساخت گروه", callback_data="group_create")],
        [InlineKeyboardButton("🔗 پیوستن به گروه", callback_data="group_join")],
        [InlineKeyboardButton("👥 گروه من", callback_data="group_my")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")],
    ])


def get_group_view_menu(is_owner):
    keyboard = [
        [InlineKeyboardButton("📤 دعوت دوست", callback_data="group_invite")],
        [InlineKeyboardButton("🔄 بروزرسانی", callback_data="group_my")],
    ]
    if is_owner:
        keyboard.append([InlineKeyboardButton("🏁 چالش جدید", callback_data="group_challenge_new")])
    keyboard.append([InlineKeyboardButton("❌ ترک گروه", callback_data="group_leave")])
    return InlineKeyboardMarkup(keyboard)


def get_group_challenge_type_menu():
    keyboard = []
    for key, info in GROUP_CHALLENGE_TYPES.items():
        keyboard.append([InlineKeyboardButton(info['name'], callback_data=f"group_ch_type_{key}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="group_my")])
    return InlineKeyboardMarkup(keyboard)


def get_group_challenge_duration_menu():
    keyboard = []
    for key, info in GROUP_CHALLENGE_DURATIONS.items():
        keyboard.append([InlineKeyboardButton(info['name'], callback_data=f"group_ch_dur_{key}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="group_my")])
    return InlineKeyboardMarkup(keyboard)


def get_subjects_menu(user_id):
    subjects = get_subjects(user_id)
    keyboard = []
    for s in subjects:
        if s['field']:
            label = f"📖 {s['book']} — {s['grade']} {s['field']}"
        else:
            label = f"📖 {s['book']} — {s['grade']}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"study_{s['id']}")])
    keyboard.append([InlineKeyboardButton("➕ افزودن درس", callback_data="add_subject")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")])
    return InlineKeyboardMarkup(keyboard)


def get_duration_menu(subject_id, chapter):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("۱ دقیقه (تست)", callback_data=f"dur_{subject_id}||{chapter}||1"),
         InlineKeyboardButton("۱۵ دقیقه", callback_data=f"dur_{subject_id}||{chapter}||15")],
        [InlineKeyboardButton("۳۰ دقیقه", callback_data=f"dur_{subject_id}||{chapter}||30"),
         InlineKeyboardButton("۶۰ دقیقه", callback_data=f"dur_{subject_id}||{chapter}||60")],
        [InlineKeyboardButton("۹۰ دقیقه", callback_data=f"dur_{subject_id}||{chapter}||90")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="menu_start_study")],
    ])


def get_answer_menu(exam_id, q_index, options):
    keyboard = []
    for i, opt in enumerate(options):
        keyboard.append([InlineKeyboardButton(f"{i+1}. {opt}",
                                              callback_data=f"ans_{exam_id}_{q_index}_{i}")])
    return InlineKeyboardMarkup(keyboard)


def get_mock_answer_menu(mock_id, q_index, options):
    keyboard = []
    for i, opt in enumerate(options):
        keyboard.append([InlineKeyboardButton(f"{i+1}. {opt}",
                                              callback_data=f"mokans_{mock_id}_{q_index}_{i}")])
    keyboard.append([InlineKeyboardButton("⏭️ رد کردن",
                                          callback_data=f"mokans_{mock_id}_{q_index}_-1")])
    return InlineKeyboardMarkup(keyboard)


def get_battle_answer_menu(battle_id, side, q_index, options):
    keyboard = []
    for i, opt in enumerate(options):
        keyboard.append([InlineKeyboardButton(f"{i+1}. {opt}",
                                              callback_data=f"btlans_{battle_id}_{side}_{q_index}_{i}")])
    return InlineKeyboardMarkup(keyboard)


def get_summaries_list_menu(summaries):
    keyboard = []
    for s in summaries:
        subj = f" — {s['subject']}" if s['subject'] else ""
        label = f"📄 {s['title']}{subj}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"summary_view_{s['id']}")])
    keyboard.append([InlineKeyboardButton("➕ خلاصه‌ی جدید", callback_data="summary_new")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="menu_summary")])
    return InlineKeyboardMarkup(keyboard)


def get_grade_select_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎓 دهم", callback_data="set_grade_دهم")],
        [InlineKeyboardButton("🎓 یازدهم", callback_data="set_grade_یازدهم")],
        [InlineKeyboardButton("🎓 دوازدهم", callback_data="set_grade_دوازدهم")],
    ])


# ============================================================
# منوهای اشتراک
# ============================================================
PLAN_NAMES = {
    "bronze": "🥉 برنزی",
    "silver": "🥈 نقره‌ای",
    "gold": "🥇 طلایی",
}

DURATION_NAMES = {
    "1m": "۱ ماهه",
    "3m": "۳ ماهه",
    "6m": "۶ ماهه",
    "12m": "۱۲ ماهه",
}


def get_subscription_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🥉 برنزی", callback_data="sub_plan_bronze")],
        [InlineKeyboardButton("🥈 نقره‌ای", callback_data="sub_plan_silver")],
        [InlineKeyboardButton("🥇 طلایی", callback_data="sub_plan_gold")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")],
    ])


def get_duration_select_menu(plan_key):
    keyboard = []
    durations = ["1m", "3m", "6m", "12m"]
    for dur_key in durations:
        price = get_plan_price_toman(plan_key, dur_key)
        if price > 0:
            label = f"{DURATION_NAMES[dur_key]} — {format_toman(price)} تومان"
            keyboard.append([InlineKeyboardButton(label, callback_data=f"sub_dur_{plan_key}_{dur_key}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="menu_subscription")])
    return InlineKeyboardMarkup(keyboard)


def get_payment_confirm_menu(plan_key, duration_key):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ پرداخت کردم", callback_data=f"sub_pay_{plan_key}_{duration_key}")],
        [InlineKeyboardButton("❌ لغو", callback_data="menu_subscription")],
    ])


def get_referral_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 بروزرسانی", callback_data="menu_referral")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")],
    ])


def get_admin_payment_menu(request_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ تایید", callback_data=f"adm_approve_{request_id}")],
        [InlineKeyboardButton("❌ رد", callback_data=f"adm_reject_{request_id}")],
    ])


# ============================================================
# منوهای پشتیبانی
# ============================================================
def get_support_menu(is_admin=False):
    keyboard = []
    if is_admin:
        keyboard.append([InlineKeyboardButton("📥 لیست کاربران", callback_data="support_admin_list")])
    keyboard.append([InlineKeyboardButton("✍️ ارسال پیام", callback_data="support_new_msg")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")])
    return InlineKeyboardMarkup(keyboard)


def get_support_admin_list_menu(users):
    keyboard = []
    for u in users:
        unread = u['unread_count'] or 0
        if unread > 0:
            label = f"🆕 {u['first_name']} — {unread} پیام جدید"
        else:
            label = f"✅ {u['first_name']}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"support_open_{u['id']}")])
    keyboard.append([InlineKeyboardButton("🔄 بروزرسانی", callback_data="support_admin_list")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")])
    return InlineKeyboardMarkup(keyboard)


def get_support_chat_menu(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✍️ پاسخ", callback_data=f"support_reply_{user_id}")],
        [InlineKeyboardButton("🔄 بروزرسانی", callback_data=f"support_open_{user_id}")],
        [InlineKeyboardButton("🔙 لیست کاربران", callback_data="support_admin_list")],
    ])


print("✅ bot_3.py (helpers + AI + menus) لود شد")
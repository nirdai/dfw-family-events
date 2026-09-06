"""
DFW Family Events Portal — Auto-Updater
========================================
רץ אוטומטית כל יום שני ב-07:00 (שעון מרכז/America-Chicago, בקירוב)
דרך GitHub Actions — לא תלוי במחשב מקומי דלוק.
פונה ל-Google Gemini API (טיר חינמי), מקבל אירועים מעודכנים לשבועות הקרובים,
וכותב את index.html החדש בשורש ה-repo — כולל רצועת התאריכים (date strip),
12 האזורים, וכפתור "היינו" (been-there) בדיוק כמו הגרסה המקורית.

איך זה רץ עכשיו:
    - .github/workflows/weekly-update.yml מפעיל את הסקריפט הזה בכל שני
    - מפתח ה-API נשמר כ-Secret בשם GEMINI_API_KEY בהגדרות ה-repo ב-GitHub
      (Settings → Secrets and variables → Actions)
    - אחרי שהסקריפט רץ, ה-workflow עושה git commit + push לשינויים
      (אם היו שינויים ב-index.html)
    - אפשר גם להריץ ידנית מלשונית Actions → Weekly DFW Events Update → Run workflow

הרצה ידנית מקומית לבדיקה (אופציונלי):
    pip install google-genai
    set GEMINI_API_KEY=...   (Windows cmd)  /  $env:GEMINI_API_KEY="..." (PowerShell)
    python update_portal.py
"""

from google import genai
import datetime
import pathlib
import sys
import os

# ── הגדרות ──────────────────────────────────────────
# נתיבים יחסיים לשורש ה-repo — כך שהסקריפט עובד גם מקומית וגם ב-GitHub Actions
OUTPUT_PATH = pathlib.Path("index.html")
LOG_PATH    = pathlib.Path("update_log.txt")
MODEL       = "gemini-3.6-flash"  # נמצא בטיר החינמי של Gemini API — ודא שזה עדיין המצב בזמן ההרצה

# 12 האזורים, לפי סדר מרחק מפלאנו (הבית) — התוויות המדויקות מוצגות ב-nav וב-view-all
REGIONS = [
    ("plano",       "פלאנו",              "כאן"),
    ("richardson",  "ריצ׳רדסון",          "~10 דק׳ · 5 מייל"),
    ("allen",       "אלן",                "~12 דק׳ · 8 מייל"),
    ("addison",     "אדיסון",             "~15 דק׳ · 9 מייל"),
    ("frisco",      "פריסקו",             "~18 דק׳ · 12 מייל"),
    ("mckinney",    "מקיני",              "~20 דק׳ · 14 מייל"),
    ("thecolony",   "The Colony",         "~20 דק׳ · 15 מייל"),
    ("lewisville",  "לואיסוויל",          "~25 דק׳ · 18 מייל"),
    ("flowermound", "פלאואר מאונד",       "~28 דק׳ · 20 מייל"),
    ("dallas",      "דאלאס / פורט וורת׳", "~30 דק׳ · 20 מייל"),
    ("irving",      "ארווינג",            "~30 דק׳ · 22 מייל"),
    ("grapevine",   "גרייפוויין",         "~35 דק׳ · 25 מייל"),
]

CATEGORIES = [
    "market", "festival", "concert", "sport", "baseball", "mlb",
    "golf", "horror", "theater", "food", "art", "race", "rodeo",
    "comedy", "film", "culture"
]

# ── Prompt ──────────────────────────────────────────
def build_prompt() -> str:
    today       = datetime.date.today()
    range_end   = today + datetime.timedelta(days=28)  # 4 שבועות קדימה
    region_list = "\n".join(f'- "{code}" = {name} ({dist})' for code, name, dist in REGIONS)
    cat_list    = ", ".join(CATEGORIES)

    return f"""
אתה עוזר שיוצר פורטל HTML של פעילויות משפחתיות לאזור דאלאס-פורט וורת', טקסס (DFW),
למשפחה שגרה בפלאנו, טקסס.

היום: {today.strftime('%A, %B %d, %Y')}
טווח לחיפוש אירועים: מהיום ועד {range_end.strftime('%B %d, %Y')} (כ-4 שבועות קדימה)

המשימה: מצא כמה שיותר אירועים מעניינים שקורים בטווח הזה, בפריסה על פני כל האזורים הבאים
(קוד האזור המדויק לשימוש בשדה region מופיע בציטוטים):
{region_list}

כללים חשובים:
- רק אירועים חד-פעמיים / עונתיים / תקופתיים: פסטיבלים, שווקים, הופעות, ירידים, מרוצים, משחקי ספורט, תערוכות, סדרות אירועים חוזרות (כמו שוק שבועי) — כן לכלול
- לא פארקים / מוזיאונים קבועים שפתוחים כל השנה בלי אירוע ספציפי
- עדיפות חזקה לאירועי סוף שבוע (שבת-ראשון), אבל אפשר גם באמצע השבוע
- כלול מרוצי NASCAR / IndyCar / Dirt Track אם יש ב-Texas Motor Speedway או באזור, משחקי MLB (Texas Rangers), Frisco RoughRiders (AA baseball), רודיאו (Fort Worth Stockyards)
- לכל אירוע תן דירוג 1-10 בהתאם לביקורות היסטוריות ורמת האטרקציה
- שדה dates הוא מערך של תאריכים בפורמט YYYY-MM-DD — אם האירוע חוזר על עצמו כמה פעמים (כמו שוק שבועי), כלול את כל התאריכים הרלוונטיים בטווח; אם זה אירוע רב-יומי (פסטיבל 3 ימים), כלול את כל הימים
- שדה weekend צריך להיות true אם לפחות אחד מהתאריכים חל בשבת/ראשון
- שדה cat חייב להיות אחד בדיוק מהרשימה הזו: {cat_list}

החזר בדיוק את קוד JavaScript הבא — מערך events בלבד, ללא backticks או הסברים, עם כמה שיותר אירועים (לפחות 25-40 אם אפשר, פרוסים על פני כל האזורים):

const events = [
  {{
    id: 1,
    region: "plano",
    cat: "festival",
    catLabel: "🎡 פסטיבל",
    weekend: true,
    dates: ["2026-09-12", "2026-09-13"],
    title: "שם האירוע",
    desc: "תיאור קצר ומשכנע בעברית — מה מיוחד, למה כדאי לבוא",
    who: "כל הגילאים",
    whenLabel: "שבת-ראשון 12-13 בספטמבר",
    hours: "10:00-18:00",
    where: "שם המקום, עיר",
    price: "חינם",
    rating: 8
  }},
];

חשוב: החזר את הקוד JavaScript בלבד, מ-const events = [ עד סגירת ];
"""

# ── HTML Template (זהה במבנה לגרסה המקורית: date strip, 12 אזורים, been-there) ──
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DFW Family Events — WEEK_LABEL</title>
<link href="https://fonts.googleapis.com/css2?family=Rubik:wght@300;400;500;700;900&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
  :root{--g0:#091510;--g2:#0f3320;--g4:#1a7a3e;--g5:#22a352;--g6:#2ecc71;--g7:#52d987;--g8:#85e8a8;--accent:#00ff88;--gold:#ffd700;--warm:#ff8c42;--wknd:#ff6b6b;--wknd-glow:rgba(255,107,107,0.3);--text:#dff5ea;--text-dim:#7bbf94;--card-bg:rgba(13,36,22,0.92);--card-border:rgba(46,204,113,0.2)}
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Rubik',sans-serif;background:var(--g0);color:var(--text);min-height:100vh;overflow-x:hidden;direction:rtl}
  body::before{content:'';position:fixed;inset:0;background:radial-gradient(ellipse 70% 50% at 15% 5%,rgba(34,163,82,.13) 0%,transparent 55%),radial-gradient(ellipse 50% 70% at 85% 85%,rgba(0,255,136,.07) 0%,transparent 55%),repeating-linear-gradient(0deg,transparent,transparent 60px,rgba(46,204,113,.022) 60px,rgba(46,204,113,.022) 61px),repeating-linear-gradient(90deg,transparent,transparent 60px,rgba(46,204,113,.022) 60px,rgba(46,204,113,.022) 61px);pointer-events:none;z-index:0}
  header{position:relative;z-index:10;padding:2.5rem 2rem 1.5rem;text-align:center;border-bottom:1px solid var(--card-border)}
  .header-badge{display:inline-block;font-family:'Space Mono',monospace;font-size:.62rem;letter-spacing:.22em;text-transform:uppercase;color:var(--accent);background:rgba(0,255,136,.07);border:1px solid rgba(0,255,136,.25);padding:.3rem 1rem;border-radius:2rem;margin-bottom:1rem}
  h1{font-size:clamp(2.2rem,6vw,4.5rem);font-weight:900;line-height:1;background:linear-gradient(135deg,var(--accent) 0%,var(--g6) 45%,var(--g8) 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:.4rem}
  .subtitle{font-size:.95rem;color:var(--text-dim);font-weight:300}
  .week-tags{display:flex;gap:.6rem;justify-content:center;margin-top:.85rem;flex-wrap:wrap}
  .wtag{font-family:'Space Mono',monospace;font-size:.68rem;padding:.28rem .85rem;border-radius:.3rem}
  .wtag.reg{color:var(--g7);background:rgba(46,204,113,.08);border:1px solid rgba(46,204,113,.25)}
  .wtag.wknd{color:var(--wknd);background:rgba(255,107,107,.1);border:1px solid rgba(255,107,107,.35);animation:pulseTag 2.5s ease-in-out infinite}
  @keyframes pulseTag{0%,100%{box-shadow:0 0 0 0 rgba(255,107,107,.2)}50%{box-shadow:0 0 0 6px rgba(255,107,107,0)}}
  .date-strip-wrap{position:relative;z-index:15;background:rgba(9,21,16,.98);border-bottom:1px solid var(--card-border);padding:.9rem 1.2rem}
  .date-strip-label{font-family:'Space Mono',monospace;font-size:.6rem;letter-spacing:.15em;text-transform:uppercase;color:var(--text-dim);text-align:center;margin-bottom:.65rem}
  .date-strip{display:flex;gap:.5rem;justify-content:center;flex-wrap:wrap}
  .date-btn{display:flex;flex-direction:column;align-items:center;gap:.15rem;padding:.45rem .7rem;border:1px solid var(--card-border);border-radius:.6rem;background:transparent;color:var(--text-dim);cursor:pointer;transition:all .2s;min-width:52px}
  .date-btn:hover{border-color:var(--g6);color:var(--g6);background:rgba(46,204,113,.06)}
  .date-btn.active-date{background:var(--g6);border-color:var(--g6);color:var(--g0);box-shadow:0 0 16px rgba(46,204,113,.5)}
  .date-btn.active-date.is-wknd-btn{background:var(--wknd);border-color:var(--wknd);box-shadow:0 0 16px var(--wknd-glow);color:#fff}
  .date-btn.is-wknd-btn:not(.active-date){border-color:rgba(255,107,107,.4);color:var(--wknd)}
  .date-btn.is-wknd-btn:not(.active-date):hover{background:rgba(255,107,107,.08)}
  .date-day{font-family:'Space Mono',monospace;font-size:.56rem;letter-spacing:.08em;text-transform:uppercase}
  .date-num{font-size:1.1rem;font-weight:700;line-height:1}
  .date-month{font-family:'Space Mono',monospace;font-size:.52rem;opacity:.75}
  .date-count{font-size:.5rem;font-family:'Space Mono',monospace;background:rgba(46,204,113,.15);border-radius:.25rem;padding:.05rem .25rem;margin-top:.05rem;color:var(--g6)}
  .active-date .date-count{background:rgba(0,0,0,.2);color:var(--g0)}
  .active-date.is-wknd-btn .date-count{color:#fff}
  .date-clear{font-size:.7rem;font-family:'Space Mono',monospace;padding:.4rem .8rem;border:1px solid rgba(255,255,255,.12);border-radius:.4rem;background:transparent;color:var(--text-dim);cursor:pointer;transition:all .2s;white-space:nowrap;align-self:center}
  .date-clear:hover{border-color:var(--accent);color:var(--accent)}
  .active-date-banner{display:none;text-align:center;font-family:'Space Mono',monospace;font-size:.68rem;padding:.45rem;background:rgba(46,204,113,.08);border-bottom:1px solid rgba(46,204,113,.15);color:var(--g7);letter-spacing:.08em}
  .active-date-banner.wknd-banner{background:rgba(255,107,107,.08);border-color:rgba(255,107,107,.2);color:#ff9a9a}
  .active-date-banner.show{display:block}
  nav{position:sticky;top:0;z-index:20;display:flex;justify-content:center;gap:.5rem;padding:.85rem 1rem;background:rgba(9,21,16,.96);backdrop-filter:blur(14px);border-bottom:1px solid var(--card-border);flex-wrap:wrap}
  .tab-btn{font-family:'Rubik',sans-serif;font-size:.78rem;font-weight:500;padding:.45rem 1rem;border:1px solid var(--card-border);border-radius:2rem;background:transparent;color:var(--text-dim);cursor:pointer;transition:all .22s;white-space:nowrap}
  .tab-btn:hover{border-color:var(--g6);color:var(--g6);background:rgba(46,204,113,.05)}
  .tab-btn .dist{font-size:.62rem;opacity:.55;font-weight:400}
  .tab-btn.active{background:var(--g6);border-color:var(--g6);color:var(--g0);font-weight:700;box-shadow:0 0 18px rgba(46,204,113,.45)}
  .tab-btn.active .dist{opacity:.75}
  main{position:relative;z-index:5;max-width:1380px;margin:0 auto;padding:1.8rem 1.4rem 5rem}
  .filter-bar{display:flex;gap:.5rem;margin-bottom:1.6rem;flex-wrap:wrap;align-items:center}
  .filter-label{font-size:.7rem;color:var(--text-dim)}
  .filter-btn{font-size:.72rem;font-weight:500;padding:.28rem .8rem;border:1px solid var(--card-border);border-radius:1.5rem;background:transparent;color:var(--text-dim);cursor:pointer;transition:all .2s}
  .filter-btn:hover{border-color:var(--g6);color:var(--g6)}
  .filter-btn.f-wknd{background:rgba(255,107,107,.12);border-color:var(--wknd);color:var(--wknd)}
  .filter-btn.f-cat{background:rgba(46,204,113,.1);border-color:var(--g6);color:var(--g6)}
  .stats-bar{display:flex;gap:.85rem;margin-bottom:2rem;flex-wrap:wrap}
  .stat-chip{background:rgba(46,204,113,.06);border:1px solid var(--card-border);border-radius:.5rem;padding:.55rem 1rem;display:flex;flex-direction:column;gap:.05rem}
  .stat-num{font-family:'Space Mono',monospace;font-size:1.25rem;font-weight:700;color:var(--accent)}
  .stat-lbl{font-size:.62rem;color:var(--text-dim);letter-spacing:.04em}
  .region-section{display:none;animation:fadeUp .35s ease}
  .region-section.active{display:block}
  @keyframes fadeUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
  .region-header{display:flex;align-items:center;gap:1rem;margin-bottom:1.6rem;padding-bottom:.9rem;border-bottom:1px solid var(--card-border)}
  .region-title{font-size:1.65rem;font-weight:700;color:var(--g6)}
  .region-drive{font-size:.82rem;font-weight:400;color:#7bbf94;opacity:.8;margin-right:.5rem;flex-shrink:0}
  .region-count{margin-right:auto;font-family:'Space Mono',monospace;font-size:.67rem;color:var(--text-dim);background:rgba(46,204,113,.07);border:1px solid var(--card-border);padding:.2rem .65rem;border-radius:1rem}
  .events-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(295px,1fr));gap:1.3rem;margin-bottom:2rem}
  .all-section-header{font-size:1.05rem;font-weight:700;color:var(--g6);margin:2rem 0 .9rem;padding-right:.6rem;border-right:3px solid var(--g6);display:flex;align-items:center;gap:.4rem}
  .event-card{background:var(--card-bg);border:1px solid var(--card-border);border-radius:.9rem;overflow:hidden;transition:transform .28s,box-shadow .28s,border-color .28s;position:relative;backdrop-filter:blur(8px)}
  .event-card:hover{transform:translateY(-5px);box-shadow:0 18px 50px rgba(46,204,113,.18);border-color:rgba(46,204,113,.55)}
  .event-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,var(--g5),var(--accent),var(--g5));opacity:0;transition:opacity .28s}
  .event-card:hover::before{opacity:1}
  .event-card.is-wknd{border-color:rgba(255,107,107,.42);background:linear-gradient(160deg,rgba(255,107,107,.06) 0%,var(--card-bg) 38%)}
  .event-card.is-wknd::before{background:linear-gradient(90deg,var(--wknd),#ff9a9a,var(--wknd));opacity:1}
  .event-card.is-wknd:hover{box-shadow:0 18px 50px rgba(255,107,107,.22);border-color:rgba(255,107,107,.7)}
  .wknd-badge{position:absolute;top:.65rem;left:.65rem;font-family:'Space Mono',monospace;font-size:.56rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;background:var(--wknd);color:#fff;padding:.2rem .5rem;border-radius:.25rem;display:flex;align-items:center;gap:.25rem;box-shadow:0 2px 10px rgba(255,107,107,.55);z-index:2}
  .card-cat{padding:.5rem 1rem;font-size:.62rem;font-family:'Space Mono',monospace;font-weight:700;letter-spacing:.13em;text-transform:uppercase;display:flex;align-items:center;gap:.4rem}
  .cat-market{background:rgba(255,215,0,.11);color:var(--gold)}
  .cat-festival{background:rgba(255,107,107,.11);color:#ff9a9a}
  .cat-concert{background:rgba(130,80,255,.11);color:#b39dff}
  .cat-sport{background:rgba(255,140,66,.11);color:var(--warm)}
  .cat-baseball{background:rgba(255,100,50,.13);color:#ff9966}
  .cat-mlb{background:rgba(20,100,200,.15);color:#66aaff}
  .cat-golf{background:rgba(100,200,100,.13);color:#90ee90}
  .cat-horror{background:rgba(120,0,180,.15);color:#cc88ff}
  .cat-theater{background:rgba(255,150,50,.11);color:#ffaa66}
  .cat-food{background:rgba(255,180,0,.11);color:#ffcc55}
  .cat-art{background:rgba(82,217,135,.13);color:var(--g7)}
  .cat-race{background:rgba(255,60,0,.13);color:#ff8060}
  .cat-rodeo{background:rgba(180,120,40,.13);color:#d4a04a}
  .cat-comedy{background:rgba(0,220,255,.09);color:#66e0ff}
  .cat-film{background:rgba(180,60,255,.09);color:#da9aff}
  .cat-culture{background:rgba(46,204,113,.12);color:var(--accent)}
  .card-body{padding:.9rem 1rem .7rem}
  .card-title{font-size:1rem;font-weight:700;color:var(--text);margin-bottom:.45rem;line-height:1.3}
  .card-title.has-badge{padding-left:2rem}
  .card-desc{font-size:.79rem;color:var(--text-dim);line-height:1.6;margin-bottom:.8rem}
  .card-meta{display:grid;grid-template-columns:1fr 1fr;gap:.32rem;margin-bottom:.8rem}
  .meta-item{display:flex;flex-direction:column;gap:.07rem;background:rgba(0,0,0,.22);border-radius:.4rem;padding:.38rem .52rem}
  .meta-label{font-size:.55rem;font-family:'Space Mono',monospace;letter-spacing:.1em;text-transform:uppercase;color:var(--g5);opacity:.85}
  .meta-value{font-size:.77rem;font-weight:500;color:var(--text)}
  .meta-item.full{grid-column:1/-1}
  .is-wknd .meta-item.date-hi{background:rgba(255,107,107,.1);border:1px solid rgba(255,107,107,.22)}
  .is-wknd .meta-item.date-hi .meta-label{color:var(--wknd)}
  .is-wknd .meta-item.date-hi .meta-value{color:#ffb0b0}
  .card-footer{display:flex;align-items:center;justify-content:space-between;padding:.65rem 1rem;border-top:1px solid rgba(46,204,113,.08);background:rgba(0,0,0,.18)}
  .rating-wrap{display:flex;align-items:center;gap:.45rem}
  .rating-dots{display:flex;gap:3px}
  .dot{width:7px;height:7px;border-radius:50%;background:var(--g2)}
  .dot.on{background:var(--g6);box-shadow:0 0 5px rgba(46,204,113,.6)}
  .dot.top{background:var(--accent);box-shadow:0 0 7px rgba(0,255,136,.7)}
  .dot.wd{background:var(--wknd);box-shadow:0 0 6px var(--wknd-glow)}
  .rating-score{font-family:'Space Mono',monospace;font-size:.88rem;font-weight:700;color:var(--accent)}
  .is-wknd .rating-score{color:#ff9a9a}
  .rating-lbl{font-size:.6rem;color:var(--text-dim)}
  .price-badge{font-size:.72rem;font-weight:600;padding:.22rem .6rem;border-radius:1rem;background:rgba(46,204,113,.08);border:1px solid rgba(46,204,113,.2);color:var(--g7);white-space:nowrap}
  .price-badge.free{background:rgba(255,215,0,.09);border-color:rgba(255,215,0,.28);color:var(--gold)}
  .price-badge.paid{background:rgba(130,80,255,.09);border-color:rgba(130,80,255,.28);color:#b39dff}
  /* BEEN THERE BUTTON */
  .event-card.been-there{border-color:rgba(255,215,0,.45) !important;background:linear-gradient(160deg,rgba(255,215,0,.05) 0%,var(--card-bg) 35%) !important}
  .event-card.been-there::before{background:linear-gradient(90deg,var(--gold),#ffe88a,var(--gold)) !important;opacity:1 !important}
  .been-btn{display:inline-flex;align-items:center;gap:.3rem;font-family:'Rubik',sans-serif;font-size:.72rem;font-weight:600;padding:.25rem .65rem;border-radius:1.5rem;border:1px solid var(--card-border);background:transparent;color:var(--text-dim);cursor:pointer;transition:all .2s;white-space:nowrap;flex-shrink:0}
  .been-btn:hover{border-color:var(--gold);color:var(--gold);background:rgba(255,215,0,.08)}
  .been-btn.checked{background:rgba(255,215,0,.15);border-color:var(--gold);color:var(--gold)}
  .event-card.hidden{display:none !important}
  .last-updated{text-align:center;font-family:'Space Mono',monospace;font-size:.6rem;color:var(--text-dim);padding:.75rem;opacity:.6;border-top:1px solid var(--card-border)}
  ::-webkit-scrollbar{width:5px}::-webkit-scrollbar-track{background:var(--g0)}::-webkit-scrollbar-thumb{background:var(--g4);border-radius:3px}
</style>
</head>
<body>
<header>
  <div class="header-badge">🗺 DFW METRO · DALLAS · TEXAS · WEEK_LABEL</div>
  <h1>פעילויות השבועיים הקרובים</h1>
  <p class="subtitle">ספורט · מרוצים · הופעות · פסטיבלים · שווקים · תיאטרון · ירידים</p>
  <div class="week-tags">
    <span class="wtag reg">📅 WEEK_RANGE</span>
    <span class="wtag wknd">🔥 סופ"ש הקרוב: WEEKEND</span>
  </div>
</header>

<div class="date-strip-wrap">
  <div class="date-strip-label">📅 סנן לפי יום ספציפי</div>
  <div class="date-strip" id="dateStrip"></div>
</div>
<div class="active-date-banner" id="activeDateBanner"></div>

<nav>
  <button class="tab-btn active" onclick="showRegion('all',this)">🌆 הכל</button>
NAV_BUTTONS
</nav>

<main>
  <div class="filter-bar">
    <span class="filter-label">סנן:</span>
    <button class="filter-btn" onclick="setFilter('wknd',this)">🔥 סופ"ש</button>
    <button class="filter-btn" onclick="setFilter(null,this)">✅ הכל</button>
    <button class="filter-btn" onclick="setFilter('mlb',this)">⚾ MLB</button>
    <button class="filter-btn" onclick="setFilter('baseball',this)">⚾ בייסבול</button>
    <button class="filter-btn" onclick="setFilter('sport',this)">⚽ ספורט</button>
    <button class="filter-btn" onclick="setFilter('rodeo',this)">🤠 רודיאו</button>
    <button class="filter-btn" onclick="setFilter('race',this)">🏁 מרוצים</button>
    <button class="filter-btn" onclick="setFilter('golf',this)">⛳ גולף</button>
    <button class="filter-btn" onclick="setFilter('concert',this)">🎸 הופעות</button>
    <button class="filter-btn" onclick="setFilter('festival',this)">🎡 פסטיבלים</button>
    <button class="filter-btn" onclick="setFilter('theater',this)">🎭 תיאטרון</button>
    <button class="filter-btn" onclick="setFilter('market',this)">🛒 שוק</button>
    <button class="filter-btn" onclick="setFilter('food',this)">🍴 אוכל</button>
    <button class="filter-btn" onclick="setFilter('horror',this)">👻 הורור</button>
    <button class="filter-btn" onclick="setFilter('free',this)">🆓 חינם</button>
  </div>
  <div class="stats-bar">
    <div class="stat-chip"><span class="stat-num" id="sTotal">0</span><span class="stat-lbl">מוצגים</span></div>
    <div class="stat-chip"><span class="stat-num" id="sWknd">0</span><span class="stat-lbl">🔥 סופ"ש</span></div>
    <div class="stat-chip"><span class="stat-num" id="sFree">0</span><span class="stat-lbl">חינמיים</span></div>
    <div class="stat-chip"><span class="stat-num" id="sTop">0</span><span class="stat-lbl">דירוג 9+</span></div>
    <button onclick="window.open('attractions.html','_blank')" style="margin-right:auto;font-family:'Rubik',sans-serif;font-size:.8rem;font-weight:600;padding:.55rem 1.1rem;border:1px solid rgba(255,215,0,.35);border-radius:.5rem;background:rgba(255,215,0,.08);color:var(--gold);cursor:pointer;transition:all .2s;white-space:nowrap" onmouseover="this.style.background='rgba(255,215,0,.18)'" onmouseout="this.style.background='rgba(255,215,0,.08)'">🗺 טיולים קבועים</button>
  </div>

  <div id="view-all" class="region-section active"></div>
  <style>.region-dist{font-family:'Space Mono',monospace;font-size:.65rem;color:var(--text-dim);background:rgba(46,204,113,.07);border:1px solid var(--card-border);padding:.2rem .6rem;border-radius:1rem;white-space:nowrap;margin-right:auto;margin-left:.5rem}</style>
REGION_SECTIONS
</main>
<div class="last-updated" id="lastUpdated">עודכן: UPDATE_TIME</div>
<script>
EVENTS_JS

const VISITED_KEY='dfw_visited_events_v1';
let visitedEvents=new Set();
try{visitedEvents=new Set(JSON.parse(localStorage.getItem(VISITED_KEY)||'[]'));}catch(e){}
function saveVisitedEvents(){try{localStorage.setItem(VISITED_KEY,JSON.stringify([...visitedEvents]));}catch(e){}}
function toggleBeenThere(id,btn,card){
  if(visitedEvents.has(id)){visitedEvents.delete(id);btn.classList.remove('checked');btn.textContent='⭕ לא היינו';card.classList.remove('been-there');}
  else{visitedEvents.add(id);btn.classList.add('checked');btn.textContent='✔ היינו!';card.classList.add('been-there');}
  saveVisitedEvents();
}

const DAYS_HE=['ראשון','שני','שלישי','רביעי','חמישי','שישי','שבת'];
const MONTHS_HE=['','ינואר','פברואר','מרץ','אפריל','מאי','יוני','יולי','אוגוסט','ספטמבר','אוקטובר','נובמבר','דצמבר'];
const WEEKEND_DAYS=[5,6,0];
let activeDate=null;

function buildDateStrip(){
  const datesSet=new Set();
  events.forEach(e=>e.dates.forEach(d=>datesSet.add(d)));
  const dates=[...datesSet].sort();
  const strip=document.getElementById('dateStrip');
  strip.innerHTML='';
  dates.forEach(dateStr=>{
    const d=new Date(dateStr+'T12:00:00');
    const dow=d.getDay();
    const isWknd=WEEKEND_DAYS.includes(dow);
    const count=events.filter(e=>e.dates.includes(dateStr)).length;
    const btn=document.createElement('button');
    btn.className='date-btn'+(isWknd?' is-wknd-btn':'');
    btn.dataset.date=dateStr;
    btn.innerHTML=`<span class="date-day">${DAYS_HE[dow]}</span><span class="date-num">${d.getDate()}</span><span class="date-month">${MONTHS_HE[d.getMonth()+1]}</span><span class="date-count">${count}</span>`;
    btn.onclick=()=>toggleDate(dateStr,btn);
    strip.appendChild(btn);
  });
  const clr=document.createElement('button');
  clr.className='date-clear';clr.textContent='✕ נקה';clr.onclick=clearDate;
  strip.appendChild(clr);
}

function toggleDate(dateStr,btn){
  if(activeDate===dateStr){clearDate();return}
  activeDate=dateStr;
  document.querySelectorAll('.date-btn').forEach(b=>b.classList.remove('active-date'));
  btn.classList.add('active-date');
  const d=new Date(dateStr+'T12:00:00');
  const dow=d.getDay();
  const isWknd=WEEKEND_DAYS.includes(dow);
  const banner=document.getElementById('activeDateBanner');
  banner.textContent=`📅 מציג: ${DAYS_HE[dow]} ${d.getDate()} ${MONTHS_HE[d.getMonth()+1]} — ${events.filter(e=>e.dates.includes(dateStr)).length} אירועים`;
  banner.className='active-date-banner show'+(isWknd?' wknd-banner':'');
  applyFilter();
}

function clearDate(){
  activeDate=null;
  document.querySelectorAll('.date-btn').forEach(b=>b.classList.remove('active-date'));
  document.getElementById('activeDateBanner').className='active-date-banner';
  applyFilter();
}

function buildCard(e){
  const isFree=e.price==='חינם'||e.price==='חינם!';
  const wc=e.weekend?' is-wknd':'';const beenCls=visitedEvents.has(e.id)?' been-there':'';
  const badge=e.weekend?`<div class="wknd-badge">🔥 סופ"ש · ${e.whenLabel}</div>`:'';
  const titleCls=e.weekend?'card-title has-badge':'card-title';
  const priceCls=isFree?'free':(e.price&&(e.price.startsWith('מ-')||e.price.startsWith('$')||e.price.startsWith('כ'))?'paid':'');
  let dots='';
  for(let i=1;i<=10;i++){const on=i<=e.rating;const cls=on?(e.rating>=9?'dot top':(e.weekend?'dot wd':'dot on')):'dot';dots+=`<div class="${cls}"></div>`;}
  return `<div class="event-card${wc}${beenCls}" data-id="${e.id}" data-region="${e.region}" data-cat="${e.cat}" data-wknd="${e.weekend?1:0}" data-free="${isFree?1:0}">
    ${badge}<div class="card-cat cat-${e.cat}">${e.catLabel}</div>
    <div class="card-body">
      <div class="${titleCls}">${e.title}</div>
      <div class="card-desc">${e.desc}</div>
      <div class="card-meta">
        <div class="meta-item${e.weekend?' date-hi':''}"><span class="meta-label">📅 מתי</span><span class="meta-value">${e.whenLabel}</span></div>
        <div class="meta-item"><span class="meta-label">⏰ שעות</span><span class="meta-value">${e.hours}</span></div>
        <div class="meta-item"><span class="meta-label">👥 מי</span><span class="meta-value">${e.who}</span></div>
        <div class="meta-item"><span class="meta-label">💰 כניסה</span><span class="meta-value">${e.price}</span></div>
        <div class="meta-item full"><span class="meta-label">📍 איפה</span><span class="meta-value">${e.where}</span></div>
      </div>
    </div>
    <div class="card-footer">
      <div class="rating-wrap"><div><div class="rating-dots">${dots}</div><div class="rating-lbl">דירוג קהילתי</div></div><div class="rating-score">${e.rating}/10</div></div>
      <span class="price-badge ${priceCls}">${e.price}</span>
      <button class="been-btn${visitedEvents.has(e.id)?' checked':''}" onclick="toggleBeenThere(${e.id},this,this.closest('.event-card'))">${visitedEvents.has(e.id)?'✔ היינו!':'⭕ לא היינו'}</button>
    </div>
  </div>`;
}

const regionNames=REGION_NAMES_JS;
const regionOrder=REGION_ORDER_JS;

let curRegion='all',curFilter=null;

function render(){
  regionOrder.forEach(r=>{
    const items=events.filter(e=>e.region===r);
    document.getElementById(`grid-${r}`).innerHTML=items.map(buildCard).join('');
    document.getElementById(`cnt-${r}`).textContent=`${items.length} אירועים`;
  });
  const av=document.getElementById('view-all');let html='';
  regionOrder.forEach(r=>{
    const items=events.filter(e=>e.region===r);
    html+=`<div class="all-section-header" id="hdr-${r}">📍 ${regionNames[r]} <span class="wknd-count" id="wc-${r}"></span></div><div class="events-grid">${items.map(buildCard).join('')}</div>`;
  });
  av.innerHTML=html;
  applyFilter();
}

function isVisible(card){
  const id=parseInt(card.dataset.id);
  const e=events.find(ev=>ev.id===id);
  if(!e)return false;
  if(activeDate&&!e.dates.includes(activeDate))return false;
  if(curRegion!=='all'&&card.dataset.region!==curRegion)return false;
  if(curFilter==='wknd'&&card.dataset.wknd!=='1')return false;
  if(curFilter==='free'&&card.dataset.free!=='1')return false;
  if(curFilter&&curFilter!=='wknd'&&curFilter!=='free'&&card.dataset.cat!==curFilter)return false;
  return true;
}

function applyFilter(){
  document.querySelectorAll('.event-card').forEach(c=>c.classList.toggle('hidden',!isVisible(c)));
  updateStats();
  regionOrder.forEach(r=>{
    const cnt=document.getElementById(`cnt-${r}`);
    const visible=document.querySelectorAll(`#grid-${r} .event-card:not(.hidden)`);
    if(cnt)cnt.textContent=`${visible.length} אירועים`;
    const wc=document.getElementById(`wc-${r}`);
    const wkndCount=[...document.querySelectorAll(`#view-all .event-card[data-region="${r}"]:not(.hidden)`)].filter(c=>c.dataset.wknd==='1').length;
    if(wc)wc.textContent=wkndCount?`${wkndCount} בסופ"ש`:'';
    if(wc)wc.style.cssText=wkndCount?'font-size:.62rem;color:var(--wknd);background:rgba(255,107,107,.1);border:1px solid rgba(255,107,107,.3);padding:.13rem .48rem;border-radius:1rem':'';
  });
}

function updateStats(){
  const visibleIds=new Set();
  document.querySelectorAll('#view-all .event-card:not(.hidden)').forEach(c=>visibleIds.add(parseInt(c.dataset.id)));
  const evs=events.filter(e=>visibleIds.has(e.id));
  document.getElementById('sTotal').textContent=visibleIds.size;
  document.getElementById('sWknd').textContent=evs.filter(e=>e.weekend).length;
  document.getElementById('sFree').textContent=evs.filter(e=>e.price==='חינם'||e.price==='חינם!').length;
  document.getElementById('sTop').textContent=evs.filter(e=>e.rating>=9).length;
}

function showRegion(r,btn){
  document.querySelectorAll('.region-section').forEach(s=>s.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
  document.getElementById(`view-${r}`).classList.add('active');
  if(btn)btn.classList.add('active');
  curRegion=r;applyFilter();
}

function setFilter(type,btn){
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('f-wknd','f-cat'));
  curFilter=curFilter===type?null:type;
  if(curFilter)btn.classList.add(type==='wknd'?'f-wknd':'f-cat');
  applyFilter();
}

buildDateStrip();
render();
</script>
</body>
</html>"""

def build_html(events_js: str) -> str:
    today       = datetime.date.today()
    week_start  = today
    week_end    = today + datetime.timedelta(days=27)
    # שבת+ראשון הקרובים (מהיום קדימה)
    days_to_sat = (5 - today.weekday()) % 7
    saturday    = today + datetime.timedelta(days=days_to_sat)
    sunday      = saturday + datetime.timedelta(days=1)

    HE_MONTHS = ["","ינואר","פברואר","מרץ","אפריל","מאי","יוני",
                 "יולי","אוגוסט","ספטמבר","אוקטובר","נובמבר","דצמבר"]
    def fmt(d): return f"{d.day} {HE_MONTHS[d.month]}"

    nav_buttons = "\n".join(
        f'  <button class="tab-btn" onclick="showRegion(\'{code}\',this)">{name}</button>'
        for code, name, _ in REGIONS
    )

    region_sections = "\n".join(
        f'  <div id="view-{code}" class="region-section"><div class="region-header">'
        f'<span style="font-size:1.8rem">📍</span><h2 class="region-title">{name}</h2>'
        f'<span class="region-drive">{dist}</span><span class="region-count" id="cnt-{code}"></span></div>'
        f'<div class="events-grid" id="grid-{code}"></div></div>'
        for code, name, dist in REGIONS
    )

    region_names_js = "{" + ",".join(f"{code}:'{name} ({dist})'" for code, name, dist in REGIONS) + "}"
    region_order_js  = "[" + ",".join(f"'{code}'" for code, _, _ in REGIONS) + "]"

    html = HTML_TEMPLATE
    html = html.replace("NAV_BUTTONS",      nav_buttons)
    html = html.replace("REGION_SECTIONS",  region_sections)
    html = html.replace("REGION_NAMES_JS",  region_names_js)
    html = html.replace("REGION_ORDER_JS",  region_order_js)
    html = html.replace("WEEK_LABEL",  f"{fmt(week_start)}–{fmt(week_end)}")
    html = html.replace("WEEK_RANGE",  f"שבוע: {fmt(week_start)}–{fmt(week_end)} {today.year}")
    html = html.replace("WEEKEND",     f"שבת {fmt(saturday)} + ראשון {fmt(sunday)}")
    html = html.replace("UPDATE_TIME", datetime.datetime.now().strftime("%d/%m/%Y %H:%M"))
    html = html.replace("EVENTS_JS",   events_js)
    return html

# ── לוג ──────────────────────────────────────────────
def log(msg: str):
    ts   = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{ts} {msg}"
    print(line)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# ── Main ──────────────────────────────────────────────
def main():
    log("▶ DFW Events Portal — עדכון שבועי")
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY לא מוגדר! הגדר כ-Secret בהגדרות ה-repo ב-GitHub.")

        log("  שולח בקשה ל-Gemini API...")
        client   = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model    = MODEL,
            contents = build_prompt()
        )
        events_js = response.text.strip()
        # Gemini לפעמים עוטף תשובות קוד ב-```js ... ``` — מסירים אם קיים
        if events_js.startswith("```"):
            events_js = events_js.split("\n", 1)[1] if "\n" in events_js else events_js
            events_js = events_js.rsplit("```", 1)[0].strip()
            if events_js.startswith("js"):
                events_js = events_js[2:].strip()
        log(f"  התקבל תגובה ({len(events_js)} תווים)")

        html = build_html(events_js)
        OUTPUT_PATH.write_text(html, encoding="utf-8")
        log(f"  ✅ נשמר בהצלחה: {OUTPUT_PATH}")

    except Exception as e:
        log(f"  ❌ שגיאה: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

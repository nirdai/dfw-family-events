# CLAUDE.md — פרויקט DFW Family Events Portal
# קרא קובץ זה בתחילת כל שיחה לפני כל עריכה

---

## מיקום קבצים
```
C:\DFIR\Personal\Code\TX\
├── index.html                    — פורטל אירועים שבועי ראשי (גם חי ב-GitHub Pages)
├── attractions.html              — דף טיולים קבועים
├── concerts.html                 — דף הופעות ומוזיקה חיה (חדש, 09/2026 — ראה סעיף ייעודי למטה)
├── update_portal.py              — סקריפט עדכון אוטומטי (רץ ב-GitHub Actions, ראה "אחסון ופריסה" למטה)
├── GITHUB_SETUP.md               — מדריך התקנה מלא (repo, Pages, Secret, בדיקה)
├── update_log.txt                — לוג ריצות (נכתב אוטומטית ע"י הסקריפט)
└── .github\workflows\
    └── weekly-update.yml         — GitHub Actions workflow שמריץ את update_portal.py כל שני
```
⚠️ `DFW_Weekly_Update.xml` (Task Scheduler הישן) הוחלף — ראה "אחסון ופריסה" למטה.
כל שלושת דפי ה-HTML מקושרים זה לזה (back-btn / כפתור בסטטס-בר) — index ⇄ attractions ⇄ concerts.

---

## בסיס — מיקום ומשפחה
- **בית:** פלאנו, טקסס
- **כל המרחקים** מחושבים מפלאנו
- **שפת הממשק:** עברית (RTL), קוד באנגלית

---

## index.html — ארכיטקטורה

### סדר טעינת JavaScript (קריטי!)
```
const events = [...] // אירועים בסיסיים (ids 1-27)

// פונקציות: buildDateStrip, buildCard, render, isVisible, applyFilter, updateStats, showRegion, setFilter

const VISITED_KEY = ...
let visitedEvents = ...
function toggleBeenThere(...)

events.push(...) // Additional events (ids 101-105, 201-212)
events.push(...) // June 8-14 events (ids 301-310)

buildDateStrip();
render(); // חייב להיות אחרי כל ה-push-ים!
```
**⚠️ render() ו-buildDateStrip() חייבים להיות בסוף — אחרי כל events.push()**

### ספירת אירועים — כלל ברזל
- `updateStats()` — סופר רק מ-`#view-all .event-card:not(.hidden)` (למניעת כפילות)
- `applyFilter()` ספירת עיר — סופר מ-`#grid-[region] .event-card:not(.hidden)` (לא לפי data-region!)
- כל כרטיס מופיע פעמיים ב-DOM: ב-`#view-all` וב-`#grid-[region]` — לכן חייבים לספור ממקום אחד

### ניווט ערים (סדר לפי מרחק מפלאנו)
| עיר | מרחק | זמן |
|-----|------|-----|
| פלאנו | 0 | כאן |
| ריצ'רדסון | 5 מייל | ~10 דק' |
| אלן | 8 מייל | ~12 דק' |
| אדיסון | 9 מייל | ~15 דק' |
| פריסקו | 12 מייל | ~18 דק' |
| מקיני | 14 מייל | ~20 דק' |
| The Colony | 15 מייל | ~20 דק' |
| לואיסוויל | 18 מייל | ~25 דק' |
| פלאואר מאונד | 20 מייל | ~28 דק' |
| דאלאס | 20 מייל | ~30 דק' |
| ארווינג | 22 מייל | ~30 דק' |
| גרייפוויין | 25 מייל | ~35 דק' |

### regionOrder (חייב להתאים לסדר לעיל)
```js
const regionOrder = ['plano','richardson','allen','addison','frisco','mckinney',
  'thecolony','lewisville','flowermound','dallas','irving','grapevine'];
```

### localStorage Keys
- `dfw_visited_events_v1` — אירועים שבועיים (index.html)
- `dfw_visited_v1` — טיולים קבועים (attractions.html)

---

## attractions.html — מקומות קבועים (18 מקומות)

| # | שם | סוג | מרחק |
|---|-----|------|-------|
| 1 | Dallas Zoo | zoo | 20 מייל |
| 2 | Fort Worth Zoo | zoo | 35 מייל |
| 3 | SEA LIFE Grapevine | aquarium | 25 מייל |
| 4 | Dallas World Aquarium | aquarium | 22 מייל |
| 5 | SeaQuest Fort Worth | aquarium | 35 מייל |
| 6 | Fossil Rim Wildlife Center | safari | 70 מייל |
| 7 | Sharkarosa Wildlife Ranch | safari | 55 מייל |
| 8 | Heard Natural Science Museum | nature | 14 מייל |
| 9 | Adriatica Village McKinney | culture | 14 מייל |
| 10 | Dinosaur Valley State Park | nature | 70 מייל |
| 11 | Medieval Times Dallas | culture | 22 מייל |
| 12 | Lone Star Park Grand Prairie | race | 28 מייל |
| 13 | In-Sync Exotics Wildlife Rescue | nature | 25 מייל |
| 14 | Dinosaur Valley RV Park | nature | 70 מייל |
| 15 | Arbor Hills Nature Preserve | nature | 3 מייל |
| 16 | Ray Roberts Lake State Park | nature | 45 מייל |
| 17 | Oak Meadow Ranch, Valley View | safari | 55 מייל |
| 18 | Revolver Brewing, Granbury | culture | 50 מייל |

### קטגוריות attractions
`zoo` | `aquarium` | `safari` | `nature` | `culture` | `race`

---

## concerts.html — הופעות ומוזיקה חיה (10 מקומות, נוסף 09/2026)

דף במבנה זהה ל-attractions.html (אותו CSS, אותה לוגיקת מעקב "היינו"), אבל localStorage key נפרד: `dfw_visited_concerts_v1` (לא להתבלבל עם `dfw_visited_v1` של attractions).

| # | שם | סוג | מרחק |
|---|-----|------|-------|
| 1 | Dos Equis Pavilion | amp | 20 מייל |
| 2 | The Pavilion at Toyota Music Factory | amp | 22 מייל |
| 3 | Concerts by the Creek — Watters Creek | lawn | 8 מייל |
| 4 | Klyde Warren Park | lawn | 20 מייל |
| 5 | Lexus Box Garden at Legacy Hall | lawn | 6 מייל |
| 6 | The Lawn at Grandscape | lawn | 15 מייל |
| 7 | Sundance Square Plaza | lawn | 35 מייל |
| 8 | Truck Yard Dallas | bar | 22 מייל |
| 9 | Truck Yard The Colony | bar | 14 מייל |
| 10 | TUPPS Brewery | bar | 14 מייל |

### קטגוריות concerts
`amp` (אמפיתיאטרון) | `lawn` (דשא ופיקניק — אפשר לשבת עם שמיכה, יש food trucks) | `bar` (בר/מבשלה עם מוזיקה חיה)

⚠️ **הערה חשובה:** בזמן המחקר לבניית הדף נמצא ש-**Lava Cantina (The Colony) נסגר** (מופיע כ-CLOSED ב-Yelp, ספטמבר 2026) — לכן לא נכלל ברשימה, למרות שבעבר היה מועמד טבעי. אם בעתיד יבדקו את הרשימה מחדש, כדאי לוודא שהמקומות עדיין פעילים לפני שמוסיפים בחזרה.

שני הדפים (attractions.html ו-concerts.html) מקושרים זה לזה עם back-btn בראש העמוד, וגם מ-index.html דרך כפתור בסטטס-בר ("🎸 הופעות ומוזיקה חיה" ליד "🗺 טיולים קבועים").

---

## עיצוב — CSS Variables
```css
--g0:#091510  /* רקע כהה */
--g6:#2ecc71  /* ירוק ראשי */
--accent:#00ff88
--gold:#ffd700
--wknd:#ff6b6b  /* אדום סופ"ש */
--text-dim:#7bbf94
--card-bg:rgba(13,36,22,0.92)
```

---

## כללי עריכה חשובים

### כשמוסיפים אירועים חדשים
- להוסיף ב-`events.push(...)` לפני `buildDateStrip(); render();`
- IDs: בסיסיים 1-27, קבוצה ראשונה 101-212, יוני 301-310
- קבוצה הבאה תתחיל מ-401

### buildCard — שדות חובה
```js
{ id, region, cat, catLabel, weekend:bool,
  dates:['YYYY-MM-DD',...],
  title, desc, who, whenLabel, hours, where,
  price, rating }
```

### price חינם — בדיקה מדויקת
```js
e.price === 'חינם' || e.price === 'חינם!'
```

### כפתור "היינו" — בכרטיס אירוע
```js
<button class="been-btn${visitedEvents.has(e.id)?' checked':''}"
  onclick="toggleBeenThere(${e.id},this,this.closest('.event-card'))">
  ${visitedEvents.has(e.id)?'✔ היינו!':'⭕ לא היינו'}
</button>
```

---

## בעיות ידועות ופתרונות

| בעיה | סיבה | פתרון |
|------|------|--------|
| ספירה כפולה | data-region מחפש בכל ה-DOM | לספור רק מ-#grid-[r] |
| אירועים לא מופיעים | render() לפני push() | להזיז render() לסוף |
| CSS לא מועיל לטקסט בתוך h2 | gradient ו-webkit-fill | להוציא span החוצה מה-h2 |
| שינויים לא נראים | דפדפן cache | סגור לגמרי ופתח מחדש |

---

## סקריפט עדכון אוטומטי
- `update_portal.py` — רץ כל שני 7:00 בבוקר
- משתמש ב-Anthropic API לעדכון אוטומטי של אירועים
- Task Scheduler: `DFW_Weekly_Update.xml`

---

## אירועים שחוזרים כל שבוע (לא צריך לחפש)
- McKinney Farmers Market — שבת 8:00-12:00 (Chestnut Square)
- Frisco Fresh Market — שבת+ראשון
- Plano Farmers Market — שבת (Willow Bend)
- Stockyards Championship Rodeo — שישי+שבת 19:30 (Cowtown Coliseum, Fort Worth)
- Concerts by the Creek Allen — שבת ערב (Watters Creek)
- Grapevine Wineries & Historic Downtown — כל יום
- Irving Farmers Market — ראשון 10:00-14:00 (Las Colinas, 501 E Las Colinas Blvd)
- Frisco RoughRiders (AA) — הומסטנדים ארוכים כל קיץ, בדוק promo schedule ל-theme nights (PAW Patrol, Skyfest זיקוקים וכו')

---

## מקורות מאומתים לעדכון (עודכן לאחר מחקר 08/2026)
כשמריצים עדכון שבועיים קדימה, אלה המקורות שהניבו תוצאות טובות בפועל — להתחיל מהם לפני חיפוש כללי:

### מקורות רב-אזוריים (הכי יעילים)
- `resident.com/amp/story/dallas/YYYY/MM/DD/the-best-things-to-do-in-dallasfort-worth-in-MMMM-YYYY` — סיכום חודשי מובנה של DFW כולל ספורט, מוזיקה, תיאטרון, שבוע מסעדות. **המקור הכי טוב שנמצא — לנסות ראשון בכל עדכון.**
- `dfwchild.com/things-to-do-this-weekend/` — אירועי סופ"ש לילדים/משפחות, מתעדכן שבועית
- `mckinneycommunitypulse.org/events-calendar/` — לוח אירועים מפורט למקיני עם תאריכים מדויקים
- `richardsontxneighbor.com/events-calendar/` — לוח אירועים מפורט לריצ'רדסון עם תאריכים מדויקים
- `grandscape.com/events/month/` — לוח חודשי מפורט ל-Grandscape/The Colony (קונצרטים, Cosm, מסעדות) — עובד טוב מאוד

### לפי עיר/מקום
- **MLB Texas Rangers**: לחפש "Texas Rangers schedule [month] [year] home games" ולקרוא מה-snippet של resident.com או dfwsportswire.com — לוח ה-ESPN/MLB.com לא נשלף טוב (JS-heavy)
- **Texas Motor Speedway**: `texasmotorspeedway.com/media/news/...schedule...` — כתבות החדשות של האתר נשלפות טוב; **באוגוסט אין מרוצים גדולים (רק "NASCAR Racing Experience" חוויית נהיגה)**
- **Frisco RoughRiders**: `milb.com/frisco/news/2026-promo-schedule` או לחפש כתבות "RoughRiders promotional schedule" — הלוח הרגיל ב-milb.com/frisco/schedule לא נשלף (JS), אבל כתבות חדשות עם התאריכים המלאים כן
- **Dos Equis Pavilion / קונצרטים בדאלאס**: מגיע דרך resident.com הכללי
- **Irving**: `irvingtexas.com/event/irving-farmers-market/...` עובד. `irvingtx.gov/special-events` לא מכיל תאריכים בפועל (רק PDF להורדה)
- **Grapevine**: `grapevinetexasusa.com/events/` לא נשלף תוכן בפועל (רק שלד עמוד) — צריך חיפוש ממוקד לפי שם אירוע

### מקורות שנכשלו / חסומים (לא לנסות שוב בלי סיבה טובה)
- `flowermound.gov/*` — robots.txt חוסם fetch. **אבל:** `flowermoundlocallife.com/events-calendar/` עובד מצוין וכיסה את פלאואר מאונד + לואיסוויל (Western Days Festival) — להשתמש בזה במקום!
- `cityoflewisville.com/*` — נשלף אך **אין אירועים מיוחדים ב-08/2026** (Sounds of Lewisville רץ רק מאי–יולי, לא באוגוסט). לספטמבר נמצא מידע דרך flowermoundlocallife.com במקום.
- `klydewarrenpark.org/viewing-schedule` ו-`/movies-in-the-park` — עמודים ריקים מתוכן בפועל (JS-rendered)
- `deepellumtexas.com/artwalk` — "self-guided", בלי תאריכים קונקרטיים
- `dallaszoo.com/after-dark/` — לא מכיל תאריכים, צריך `dallaszoo.com/dallas-zoo-events/calendar/`
- `friscotexas.gov/221/Special-Events` — עובד טוב (בניגוד לחודש הקודם), מכיל אירועי עירייה (לא רק פסטיבלים)
- **The Colony / Lewisville / Flower Mound** היו ריקים בסבב הראשון של אוגוסט 2026, אבל **בספטמבר נמצאו אירועים טובים לכולם** (Grandscape ל-The Colony, flowermoundlocallife.com ל-Lewisville+Flower Mound) — המסקנה: אם עיר "ריקה" בסבב מסוים, לנסות שוב בסבב הבא עם URLs חדשים, לא לוותר לצמיתות.

### מקורות נוספים שהוכיחו את עצמם (עדכון 09/2026)
- `dallas.culturemap.com/news/entertainment/labor-day-weekend-events-2026/` (ותבנית דומה ל-"[holiday]-weekend-events-[year]") — נשלף מעולה, מפורט לפי תאריך
- `www.dallasites101.com/blog/post/...` — כתבות "things to do" עם תאריכים ומיקומים מדויקים, כולל Labor Day, GrapeFest ועוד
- `fortworthstockyards.org/events/...` — לוח אירועים ספציפי לחגים (Giddy Up & Go, Labor Day) עובד טוב
- `www.fortworth.com/blog/stories/post/september-things-to-do/` — סיכום חודשי ל-Fort Worth (מקביל ל-resident.com לדאלאס)
- `planomagazine.com/things-to-do-this-MONTH-YY/` — סיכום חודשי מפורט ומצוין לפלאנו (תאריכים, מחירים, מיקומים)
- `visitallentexas.com/events/` — עובד טוב לאלן
- `flowermoundlocallife.com/events-calendar/` — מצוין לפלאואר מאונד **וגם** ללואיסוויל (מכסה את שתי הערים)
- `grandscape.com/events/month/` — ממשיך לעבוד מצוין (The Colony), נותן עשרות אירועים לחודש

### אירועים שנתיים גדולים לזכור לשנה הבאה (לא רק ל-2026)
- **GrapeFest** (Grapevine) — בדרך כלל ~שבוע 3 של ספטמבר, פסטיבל היין הגדול בטקסס
- **Addison Oktoberfest** — בדרך כלל ~שבוע 3 של ספטמבר, Addison Circle Park
- **McKinney Oktoberfest** — בדרך כלל ~שבוע האחרון של ספטמבר
- **Plano Balloon Festival** — בדרך כלל ~שבוע 3 של ספטמבר, Oak Point Event Field
- **State Fair of Texas** — נפתח בדרך כלל בסוף ספטמבר (השנה 25/9), נמשך כ-24 יום עד אמצע אוקטובר, Fair Park
- **Autumn at the Arboretum (Pumpkin Village)** — נפתח בדרך כלל ~19-20 בספטמבר, נמשך עד תחילת נובמבר
- **Frisco RoughRiders** — אם זוכים באליפות מחצית, הפלייאוף מתחיל ~אמצע ספטמבר (בדוק "RoughRiders playoff tickets" כל שנה)

---

## אחסון ופריסה (09/2026) — GitHub Pages + GitHub Actions

האתר עבר משלב "קובץ מקומי על המחשב" לאתר חי, זמין 24/7 ונגיש מכל מכשיר (כולל טלפון).

### מה השתנה
| מה | לפני | אחרי |
|-----|------|------|
| אחסון האתר | פתיחת `index.html` מקומית על המחשב | **GitHub Pages** — `https://nirdai.github.io/dfw-family-events/` |
| מנוע ה-repo | לא היה Git | **GitHub repo:** `nirdai/dfw-family-events` (Public — נדרש ל-Pages בחינם) |
| עדכון שבועי אוטומטי | Windows Task Scheduler מקומי (`DFW_Weekly_Update.xml`, שני 7:00, דורש שהמחשב דלוק) | **GitHub Actions** (`.github\workflows\weekly-update.yml`) — רץ בענן של GitHub, ~12:00 UTC (07:00 טקסס בשעון קיץ) בכל שני, לא תלוי במחשב האישי |
| ספק ה-AI ליצירת אירועים | Anthropic API (`ANTHROPIC_API_KEY`, מודל `claude-sonnet-4-6`) — דרש כרטיס אשראי/תשלום | **Google Gemini API — טיר חינמי** (`GEMINI_API_KEY`), חבילת פייתון `google-genai` (`from google import genai`) |
| שם המודל בפועל | claude-sonnet-4-6 | **`gemini-3.6-flash`** (הוחלף מ-`gemini-2.5-flash` אחרי ש-Google הפסיקו לתת גישה למשתמשים חדשים לדגם הזה — קיבלנו שגיאת 404 עם המלצה מפורשת לעבור ל-3.6-flash) |
| הפעלה ידנית לבדיקה | הרצת הסקריפט ידנית ב-Python על המחשב | לשונית **Actions** ב-repo → Weekly DFW Events Update → **Run workflow** |

### הגדרות קריטיות שהוגדרו ב-GitHub (לא בקוד — לזכור אם צריך לשחזר בעתיד)
- **Secret:** `GEMINI_API_KEY` — תחת Settings → Secrets and variables → Actions ב-repo
- **Pages:** Settings → Pages → Source: Deploy from a branch → Branch `main` → תיקייה `/ (root)`
- מפתח ה-Gemini נוצר ב-https://aistudio.google.com/apikey (חינמי לגמרי, בלי כרטיס אשראי)

### תקלות שנתקלנו בהן בדרך (למקרה שיחזרו)
1. **`git push` נכשל עם "Repository not found"** — ה-repo לא נוצר עדיין בפועל ב-GitHub לפני ניסיון ה-push. פתרון: ליצור את ה-repo תחילה ב-github.com/new.
2. **`git remote add origin` נכשל עם "remote origin already exists"** — היה כבר remote מהגדרה קודמת. פתרון: `git remote set-url origin <url>` במקום `add`.
3. **לא ניתן היה לכתוב ישירות ל-`.github\workflows\` דרך כלי הגישה המרוחקת ל-מחשב** (תיקייה מוגנת) — נכתב לשורש התיקייה ונדרשה הזזה ידנית (`move`) ל-`.github\workflows\weekly-update.yml`.
4. **סנכרון בין קובץ ה-workflow שהוזז ל-`.github\workflows\` לבין גרסאות מעודכנות** — כשעדכנו את ה-workflow (מ-Anthropic ל-Gemini) אחרי שהוא כבר הוזז, הגרסה החדשה נכתבה שוב לשורש בלבד ולא דרסה את זו שכבר הוזזה. גרם ל-`ModuleNotFoundError: No module named 'google'` (ה-workflow הישן עוד התקין `anthropic`, אבל הסקריפט כבר ציפה ל-`google-genai`). פתרון: לוודא תמיד ש-`.github\workflows\weekly-update.yml` עצמו מעודכן, לא רק עותק בשורש.
5. **`ModuleNotFoundError: No module named 'google'`** — ראה תקלה 4 למעלה.
6. **שגיאת 404 `models/gemini-2.5-flash is no longer available to new users`** — Google הפסיקו גישה חדשה לדגם הזה. פתרון: החלפה ל-`gemini-3.6-flash` (השם שה-API עצמו המליץ עליו בהודעת השגיאה).
7. **⚠️ הטעות המשמעותית ביותר (09/2026): התבנית ב-`update_portal.py` דרסה תכונות אמיתיות באתר.** כשנבנה לראשונה `update_portal.py` (וגם בגרסת ה-Gemini הראשונה), ה-HTML_TEMPLATE שלו היה גרסה **הרבה יותר פשוטה** מ-`index.html` האמיתי שכבר היה קיים — בלי רצועת תאריכים (`buildDateStrip`), בלי כפתור "היינו", ורק 5 אזורים במקום 12. כשה-workflow רץ בהצלחה בפעם הראשונה, הוא **דרס בשקט** את `index.html` העשיר עם הגרסה המרוקנת — התוצאה: המשתמש דיווח ש"אי אפשר לעבור בין תאריכים, הם לא מוצגים בכלל" (חשב שזה "באג בטלפון", אבל למעשה זה היה קורה בכל מכשיר, כי הפיצ'ר פשוט נמחק מהאתר החי). **לקח לזכור:** לפני שכותבים סקריפט אוטומציה שמייצר/מחליף קובץ קיים, **תמיד להשוות את הפלט של הסקריפט מול הקובץ הקיים בפועל** (לא רק להניח שהמבנה דומה) — כדי לוודא שאין תכונות שהולכות לאיבוד. תוקן ב-06/09/2026: `update_portal.py` שוכתב כך שהתבנית תואמת בדיוק למבנה המקורי (date strip + 12 אזורים + been-there).
8. **`git pull -X ours` פתח עורך Vim לא צפוי** — כש-git צריך למזג ודורש הודעת commit, הוא פותח את עורך ברירת המחדל (Vim על MINGW64/Git Bash) — משתמש שלא מכיר Vim לא ידע לצאת ממנו (`Esc` ואז `:wq`). **לקח לזכור לעתיד:** לפני שנותנים למשתמש פקודת git שעלולה לפתוח עורך אינטראקטיבי (merge בלי `-m`, `rebase -i` וכו'), או תמיד לצרף `-m "..."` מראש כדי להימנע מפתיחת עורך, או להסביר מראש בדיוק איך לצאת ממנו.
9. **⚠️ `-X ours` לא עשה כלום בפועל — ולא בדקתי את זה מראש.** ההמלצה על `git pull -X ours` הייתה שגויה מיסודה: `-X ours`/`-X theirs` משפיע **רק** על hunk-ים שבאמת מתנגשים (שני הצדדים שינו את אותו קטע). אבל כאן ה-`index.html` המקומי מעולם לא השתנה מאז ה-commit הראשוני — רק הצד המרוחק (ה-GitHub Action) שינה אותו. לכן ה-merge של git ראה שינוי **חד-צדדי בלבד**, ואין "קונפליקט" לפתור — git פשוט החיל את השינוי המרוחק (הגרסה הפשוטה) בלי לשאול, ו-`-X ours` לא הייתה רלוונטית בכלל. התוצאה: הבעיה חזרה בדיוק כפי שהייתה, אחרי שכבר "תוקנה" כביכול. **לקח קריטי:** לפני שממליצים על כל דגל/פרמטר git (`-X ours`, `--force`, `-X theirs` וכו') — לוודא שמבינים בדיוק באילו תנאים הוא פועל, ולא להניח שהוא "יפתור את זה" רק כי השם נשמע מתאים. **באופן כללי: לחשוב על כל התהליך עד הסוף — כולל מה בדיוק ההיסטוריה של הקבצים בכל צד (local HEAD מול remote HEAD מול working directory), מה בדיוק תעשה כל פקודה בהינתן ההיסטוריה הזו, ואילו תרחישי קצה יכולים לקרות — לפני שממליצים על פקודה למשתמש, ולא לתקן טעות עם עוד ניחוש.**

### איך מעדכנים את האתר בעתיד
1. עריכת קבצים מקומית (`index.html`, `attractions.html`, `update_portal.py` וכו')
2. `git add . && git commit -m "..." && git push`
3. GitHub Pages מתעדכן אוטומטית תוך דקה-שתיים — אין צורך לגעת בהגדרות שוב
4. אם `MODEL` ב-`update_portal.py` מפסיק לעבוד (כמו שקרה עם `gemini-2.5-flash`) — לבדוק את רשימת הדגמים החינמיים העדכנית ב-https://ai.google.dev/gemini-api/docs/pricing ולעדכן את המשתנה

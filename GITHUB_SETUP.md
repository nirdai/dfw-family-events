# הפיכת אתר האירועים לזמין תמיד ונגיש מהטלפון

מדריך צעד-אחר-צעד להעלאת האתר ל-GitHub Pages (חינמי, זמין 24/7, נגיש מכל מכשיר) והעברת העדכון האוטומטי השבועי מהמחשב שלך ל-GitHub Actions (רץ בענן, גם אם המחשב כבוי).

קבצים חדשים שנוספו לתיקייה `C:\DFIR\Personal\Code\TX\`:
- `weekly-update.yml` — מגדיר את הריצה האוטומטית השבועית בענן (**צריך להעביר ידנית ל-`.github\workflows\weekly-update.yml`** — ראה שלב 0 למטה; לא ניתן היה לכתוב ישירות לתיקיית `.github` דרך הכלים המרוחקים)
- `update_portal.py` — עודכן: נתיבי קבצים יחסיים במקום נתיבי Windows (כדי שירוץ גם ב-GitHub)
- מדריך זה (`GITHUB_SETUP.md`)

---

## שלב 0 — הזזת קובץ ה-workflow למקום הנכון

GitHub Actions דורש שקובצי ה-workflow יהיו בתיקייה `.github\workflows\`. פתח סייר הקבצים (או שורת פקודה) בתוך `C:\DFIR\Personal\Code\TX\` וצור את מבנה התיקיות:

```powershell
mkdir .github\workflows
move weekly-update.yml .github\workflows\weekly-update.yml
```

(אפשר גם ידנית: צור תיקייה בשם `.github`, בתוכה תיקייה `workflows`, וגרור את `weekly-update.yml` פנימה)

## שלב 1 — יצירת Repository ב-GitHub

1. היכנס ל-https://github.com/new
2. שם מוצע: `dfw-family-events` (אפשר גם שם אחר)
3. **Visibility: Public** — כדי ש-GitHub Pages יעבוד בחינם (Private דורש תוכנית בתשלום ל-Pages)
4. **אל תסמן** "Add a README file" — יש לך כבר קבצים מקומיים
5. לחץ **Create repository**

## שלב 2 — חיבור התיקייה המקומית ודחיפה ל-GitHub

פתח שורת פקודה (PowerShell או Git Bash) בתוך `C:\DFIR\Personal\Code\TX\` והרץ:

```bash
git init
git add .
git commit -m "Initial commit: DFW family events portal"
git branch -M main
git remote add origin https://github.com/<שם-המשתמש-שלך>/dfw-family-events.git
git push -u origin main
```

(אם `git` לא מותקן: הורד מ-https://git-scm.com/download/win)

## שלב 3 — הפעלת GitHub Pages

1. ב-repo ב-GitHub: **Settings → Pages**
2. תחת **Source** בחר **Deploy from a branch**
3. Branch: **main**, תיקייה: **/ (root)**
4. **Save**
5. אחרי דקה-שתיים האתר יהיה זמין בכתובת:
   `https://<שם-המשתמש-שלך>.github.io/dfw-family-events/`

זו הכתובת שתוכל לפתוח מהטלפון, לשמור כקיצור במסך הבית, ולשלוח למשפחה.

## שלב 4 — קבלת מפתח Gemini API חינמי והגדרתו כ-Secret

**קבלת המפתח (חינמי, בלי כרטיס אשראי):**
1. גש ל-https://aistudio.google.com/apikey
2. התחבר עם חשבון Google
3. **Create API key** → בחר פרויקט (או צור חדש) → המפתח יופיע מיד
4. העתק את המפתח (מחרוזת ארוכה, לא מתחילה ב-`sk-`)

**הגדרה כ-Secret ב-GitHub:**
1. ב-repo: **Settings → Secrets and variables → Actions**
2. **New repository secret**
3. Name: `GEMINI_API_KEY`
4. Value: המפתח שהעתקת מ-AI Studio
5. **Add secret**

הטיר החינמי של Gemini (דגם `gemini-2.5-flash`) כולל כמות נדיבה של בקשות ביום — עדכון אחד בשבוע רחוק מאוד מהמכסה, כך שזה אמור להישאר חינמי לחלוטין.

## שלב 5 — בדיקה ידנית של העדכון האוטומטי

1. בלשונית **Actions** ב-repo, בחר **Weekly DFW Events Update**
2. **Run workflow → Run workflow** (הפעלה ידנית, לא צריך לחכות לשני)
3. עקוב אחרי הריצה — אם הצליחה, `index.html` יתעדכן אוטומטית ויידחף ל-repo, והאתר החי יתעדכן תוך דקה

## שלב 6 — ניקוי: כיבוי המשימה הישנה ב-Task Scheduler

עכשיו שהעדכון רץ בענן, אפשר לבטל את המשימה הישנה במחשב:
1. פתח **Task Scheduler**
2. מצא את המשימה `DFW_Weekly_Update`
3. לחיצה ימנית → **Disable** (או Delete)

---

## הערות

- **המודל ב-`update_portal.py`** מוגדר כרגע ל-`gemini-2.5-flash` (בטיר החינמי) — אם בעתיד המודל הזה יוצא משימוש, אפשר לעדכן את שם המשתנה `MODEL` בקובץ לשם מודל Gemini עדכני מרשימת הדגמים החינמיים ב-https://ai.google.dev/gemini-api/docs/pricing.
- Gemini לפעמים מחזיר את הקוד עטוף ב-```` ```js ... ``` ```` — הסקריפט כבר מנקה את זה אוטומטית, אבל אם ה-`index.html` נראה שבור אחרי עדכון, זה המקום הראשון לבדוק (הדפסת `update_log.txt` תראה מה בדיוק חזר).
- כדי לעדכן את האתר בעתיד (למשל להוסיף עיר חדשה או לשנות עיצוב) — פשוט תערוך את הקבצים המקומיים ותריץ שוב `git add . && git commit -m "..." && git push`. GitHub Pages יתעדכן אוטומטית.
- אם בעתיד תרצה דומיין מותאם אישית (כמו `dfwevents.com` במקום `github.io`) — אפשר להוסיף אותו תחת Settings → Pages → Custom domain.

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

## שלב 4 — הגדרת מפתח ה-API כ-Secret (לעדכון האוטומטי)

1. ב-repo: **Settings → Secrets and variables → Actions**
2. **New repository secret**
3. Name: `ANTHROPIC_API_KEY`
4. Value: מפתח ה-API שלך (אותו מפתח ששימש את Task Scheduler)
5. **Add secret**

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

- **המודל ב-`update_portal.py`** מוגדר כרגע ל-`claude-sonnet-4-6` — כדאי לוודא בזמן ההרצה הראשונה שזה שם מודל תקף בחשבון ה-API שלך; אם הריצה ב-Actions נכשלת עם שגיאת מודל, זה המקום הראשון לבדוק.
- כדי לעדכן את האתר בעתיד (למשל להוסיף עיר חדשה או לשנות עיצוב) — פשוט תערוך את הקבצים המקומיים ותריץ שוב `git add . && git commit -m "..." && git push`. GitHub Pages יתעדכן אוטומטית.
- אם בעתיד תרצה דומיין מותאם אישית (כמו `dfwevents.com` במקום `github.io`) — אפשר להוסיף אותו תחת Settings → Pages → Custom domain.

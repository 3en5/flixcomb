# FlixComb

מסנן תכנים ביתי לנטפליקס בשיטת **רשימת היתרים**: בפרופיל המסונן מופיעים רק
כותרים שאישרת, וכל השאר נחסם.

FlixComb בונה את קטלוג נטפליקס בישראל (מ-TMDB) ושומר אילו כותרים אישרת לכל
פרופיל. לפי זה הוא מחשב מה צריך להגדיר בבקרת ההורים של הפרופיל בנטפליקס:
את תקרת דירוג הגיל ואת רשימת הכותרים לחסימה. את התכנון המלא אפשר למצוא ב-[docs/PLAN.md](docs/PLAN.md).

## התקנה

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

צריך גם מפתח TMDB. החשבון חינמי: נרשמים ב-themoviedb.org, נכנסים ל-Settings ואז ל-API,
ומעתיקים את ה-**API Read Access Token**.

```bash
export TMDB_TOKEN=...
```

## שימוש

```bash
flixcomb sync                         # סנכרון הקטלוג (הפעם הראשונה לוקחת כמה דקות)
flixcomb search "bluey"               # חיפוש כותר, מחזיר מזהה כמו tv:82728
flixcomb approve kids tv:82728        # אישור כותר לפרופיל kids
flixcomb approve kids movie:8587 --age 7   # אישור עם תיקון של הגיל המוערך
flixcomb approved kids                # הכותרים שאושרו
flixcomb revoke kids movie:8587       # ביטול אישור
flixcomb plan kids                    # תקרת הגיל ורשימת הכותרים לחסימה
flixcomb plan kids --format csv > block.csv
```

את מה ש-`plan` מדפיס מגדירים בנטפליקס, באתר:
**חשבון ← פרופיל ← בקרת הורים**. שם קובעים את תקרת הגיל ומוסיפים את הכותרים
ל-Title Restrictions. בשלב הבא העדכון הזה יהיה אוטומטי.

אל תשכח לנעול עם PIN את שאר הפרופילים בחשבון.

## בדיקת היתכנות: כמה כותרים נטפליקס מסכימה לחסום

`flixcomb probe` פותח דפדפן, מוסיף כותרים ל-Title Restrictions של פרופיל, שומר
כל 50 כותרים, טוען את הדף מחדש ובודק שכל הכותרים שנשמרו עדיין שם. אם חלק מהם
נעלמו, כנראה הגענו למגבלה, והסקריפט עוצר ומדווח.

**חשוב:** להריץ רק על **פרופיל ניסיון** חדש. בסוף אפשר פשוט למחוק אותו.

הסקריפט רץ על המחשב שלך, כי הוא צריך את הדפדפן שבו אתה מחובר לנטפליקס.
צריך להתקין [Python](https://www.python.org/downloads/) (בהתקנה מסמנים את
"Add python.exe to PATH") וגם [Git](https://git-scm.com/download/win). אחר כך,
ב-PowerShell:

```powershell
git clone https://github.com/3en5/flixcomb
cd flixcomb
py -m venv .venv
.venv\Scripts\pip install -e ".[netflix]"
.venv\Scripts\playwright install chromium
.venv\Scripts\flixcomb probe --titles titles.txt --count 500
```

`titles.txt` הוא קובץ עם שם של כותר אחד בכל שורה, בשפת הממשק של חשבון
הנטפליקס. אם כבר הרצת `sync` אפשר לוותר על `--titles`, ואז הכותרים נלקחים
מהקטלוג.

מה יקרה:
1. ייפתח דפדפן. **אתה** מתחבר לנטפליקס, והסיסמה לא נשמרת אצל FlixComb.
2. נכנסים לבקרת ההורים של פרופיל הניסיון ועוצרים כשתיבת החיפוש של
   Title Restrictions מופיעה. חוזרים לחלון של PowerShell ולוחצים Enter.
3. הסקריפט מוסיף את הכותרים בעצמו. אם נטפליקס מבקשת שוב סיסמה, הוא יעצור
   ויחכה לך.
4. התוצאות נשמרות בתיקייה `probe-output`: קובץ `report.json` וצילומי מסך.
   את הקבצים האלה שולחים לי.

אם הסקריפט לא מוצא את תיבת החיפוש, הוא שומר צילום מסך ואת קוד הדף, בשמות
`no_input.png` ו-`no_input.html`. איתם אוכל להתאים אותו לממשק של נטפליקס.

## הגדרות (משתני סביבה)

| משתנה | ברירת מחדל | |
|---|---|---|
| `TMDB_TOKEN` | | חובה בשביל `sync` |
| `FLIXCOMB_DB` | `flixcomb.db` | קובץ מסד הנתונים |
| `FLIXCOMB_REGION` | `IL` | המדינה של חשבון הנטפליקס |
| `FLIXCOMB_LANGUAGE` | `he-IL` | שפת שמות הכותרים |

## בדיקות

```bash
.venv/bin/pytest
```

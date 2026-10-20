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

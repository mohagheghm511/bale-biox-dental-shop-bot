"""
تبدیل تاریخ میلادی به شمسی
ساعت از سیستم محلی گرفته میشه — نیازی به تبدیل timezone نیست
"""
from datetime import datetime

try:
    import jdatetime
    _HAS_JDATE = True
except ImportError:
    _HAS_JDATE = False


def _parse_dt(date_str: str) -> datetime:
    """تبدیل رشته تاریخ به datetime"""
    ds = str(date_str).strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(ds[:len(fmt.replace("%Y","0000").replace("%m","00").replace("%d","00").replace("%H","00").replace("%M","00").replace("%S","00"))], fmt)
        except:
            pass
    # fallback
    try:
        return datetime.strptime(ds[:19], "%Y-%m-%d %H:%M:%S")
    except:
        try:
            return datetime.strptime(ds[:10], "%Y-%m-%d")
        except:
            return datetime.now()


def _parse_dt(date_str: str) -> datetime:
    ds = str(date_str).strip().replace("T", " ")
    for fmt, ln in [("%Y-%m-%d %H:%M:%S", 19), ("%Y-%m-%d %H:%M", 16), ("%Y-%m-%d", 10)]:
        try:
            return datetime.strptime(ds[:ln], fmt)
        except:
            pass
    return datetime.now()


def to_jalali(date_str: str, show_time: bool = False) -> str:
    """تبدیل رشته تاریخ میلادی به شمسی"""
    if not date_str:
        return "-"
    try:
        # اگه از قبل شمسیه (شامل /)
        ds = str(date_str).strip()
        if ds.count('/') >= 2:
            return ds[:16] if show_time else ds[:10]

        dt = _parse_dt(ds)

        if not _HAS_JDATE:
            if show_time:
                return dt.strftime("%Y-%m-%d %H:%M")
            return dt.strftime("%Y-%m-%d")

        jd = jdatetime.datetime.fromgregorian(
            year=dt.year, month=dt.month, day=dt.day,
            hour=dt.hour, minute=dt.minute
        )
        date_fa = f"{jd.year}/{jd.month:02d}/{jd.day:02d}"
        if show_time:
            return f"{date_fa} - {jd.hour:02d}:{jd.minute:02d}"
        return date_fa
    except Exception as e:
        return str(date_str)[:10]


def now_jalali(show_time: bool = True) -> str:
    """تاریخ و ساعت الان به شمسی (از ساعت سیستم)"""
    now = datetime.now()
    if not _HAS_JDATE:
        fmt = "%Y-%m-%d %H:%M" if show_time else "%Y-%m-%d"
        return now.strftime(fmt)
    jd = jdatetime.datetime.fromgregorian(
        year=now.year, month=now.month, day=now.day,
        hour=now.hour, minute=now.minute
    )
    date_fa = f"{jd.year}/{jd.month:02d}/{jd.day:02d}"
    if show_time:
        return f"{date_fa} - {jd.hour:02d}:{jd.minute:02d}"
    return date_fa


def today_jalali() -> str:
    return now_jalali(show_time=False)


def iran_now_str() -> str:
    """ساعت الان (از سیستم) برای ذخیره در دیتابیس — HH:MM:SS"""
    return datetime.now().strftime("%H:%M:%S")


def iran_now_datetime_str() -> str:
    """تاریخ+ساعت الان (از سیستم)"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

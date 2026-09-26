from utils.date_utils import to_jalali
"""
ساخت فایل اکسل و ارسال برای ادمین
"""
import io
import json
from datetime import datetime

def _workbook():
    try:
        import openpyxl
        return openpyxl
    except ImportError:
        return None

async def send_customers_excel(bot, admin_id):
    """خروجی اکسل اطلاعات مشتریان (یک هفته اخیر)"""
    xl = _workbook()
    if not xl:
        await bot.send_message(admin_id, "لطفاً openpyxl را نصب کنید:\npip install openpyxl")
        return

    from database.db import get_customers_with_orders
    customers = get_customers_with_orders()

    wb = xl.Workbook()
    ws = wb.active
    ws.title = "مشتریان"

    headers = ["نام کامل","نام حقیقی","کد ملی","شماره موبایل","تلفن ثابت",
               "آدرس","کد پستی","کد نظام پزشکی","تاریخ تولد","سمت",
               "تعداد سفارش","مجموع خرید"]
    ws.append(headers)

    for c in customers:
        ws.append([
            c["full_name"] or "",
            c["real_name"] or "",
            c["national_id"] or "",
            c["phone"] or "",
            c["landline"] or "",
            c["address"] or "",
            c["postal_code"] or "",
            c["medical_code"] or "",
            c["birth_date"] or "",
            c["role"] or "",
            c["order_count"] or 0,
            c["total_spent"] or 0,
        ])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    from bale import InputFile
    fname = f"customers_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    await bot.send_document(admin_id, InputFile(buf.read(), file_name=fname),
                            caption=f"اطلاعات مشتریان\nتاریخ: {datetime.now().strftime('%Y/%m/%d')}")


async def send_orders_excel(bot, admin_id, days):
    """خروجی اکسل سفارشات برای بازه زمانی"""
    xl = _workbook()
    if not xl:
        await bot.send_message(admin_id, "لطفاً openpyxl را نصب کنید:\npip install openpyxl")
        return

    from database.db import get_orders_by_period
    orders = get_orders_by_period(days)

    wb = xl.Workbook()
    ws = wb.active
    period_map = {30:"۱ ماه", 90:"۳ ماه", 180:"۶ ماه", 365:"۱ سال"}
    ws.title = f"سفارشات {period_map.get(days,'')}"

    headers = ["شماره سفارش","نام مشتری","نام حقیقی","کد ملی","موبایل",
               "آدرس","کد پستی","کد نظام پزشکی","محصولات",
               "مبلغ کل","تخفیف","مبلغ نهایی","وضعیت","تاریخ"]
    ws.append(headers)

    total_revenue = 0
    for o in orders:
        try:
            items = json.loads(o["items"])
            items_txt = " | ".join(f"{i['catalog_code']}×{i['qty']}" for i in items)
        except:
            items_txt = ""
        ws.append([
            o["order_number"],
            o["full_name"] or "",
            o["real_name"] or "",
            o["national_id"] or "",
            o["phone"] or "",
            o["address"] or "",
            o["postal_code"] or "",
            o["medical_code"] or "",
            items_txt,
            o["total_amount"],
            o["discount_amount"],
            o["final_amount"],
            o["status"],
            to_jalali(o["created_at"]),
        ])
        total_revenue += o["final_amount"] or 0

    # خلاصه
    ws.append([])
    ws.append(["جمع کل درآمد:", "", "", "", "", "", "", "", "", "", "", total_revenue])
    ws.append(["تعداد سفارشات:", len(orders)])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    from bale import InputFile
    fname = f"orders_{days}days_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    period_fa = period_map.get(days, str(days))
    await bot.send_document(admin_id, InputFile(buf.read(), file_name=fname),
                            caption=f"گزارش سفارشات {period_fa} گذشته\n"
                                    f"تعداد: {len(orders)}\n"
                                    f"درآمد: {total_revenue:,} تومان")

from utils.date_utils import to_jalali
from database.db import get_user, get_user_orders

STATUS_FA = {
    "pending_payment": "💳 در انتظار پرداخت",
    "receipt_sent":    "🔍 در حال بررسی",
    "approved":        "✅ تأیید شده",
    "rejected":        "❌ رد شده",
    "shipped":         "🚚 ارسال شده",
}


async def cmd_account(bot, message):
    bale_id = int(message.author.user_id)
    user = get_user(bale_id)
    if not user or not user["full_name"]:
        await message.reply("❌ لطفاً ابتدا /start را بزنید.")
        return

    orders = get_user_orders(bale_id)

    # محاسبه بدهی
    total_debt = 0
    paid_total = 0
    for o in orders:
        if o["status"] == "approved":
            paid_total += o["final_amount"]
        elif o["status"] in ("pending_payment", "receipt_sent"):
            total_debt += o["final_amount"]

    txt = (
        f"👤 *حساب کاربری*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 نام: {user['full_name']}\n"
        f"📱 موبایل: {user['phone'] or '-'}\n"
        f"🏥 سمت: {user['role'] or '-'}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📦 تعداد سفارش‌ها: {len(orders)}\n"
        f"✅ پرداخت شده: {paid_total:,} تومان\n"
        f"💳 بدهی جاری: {total_debt:,} تومان\n"
        f"━━━━━━━━━━━━━━━\n"
        f"*آخرین سفارش‌ها:*\n"
    )

    if not orders:
        txt += "سفارشی ثبت نشده."
    else:
        for o in orders[:5]:
            st = STATUS_FA.get(o["status"], o["status"])
            txt += (
                f"\n🔢 {o['order_number']}\n"
                f"   وضعیت: {st}\n"
                f"   مبلغ: {o['final_amount']:,} تومان\n"
                f"   تاریخ: {to_jalali(o['created_at'])}\n"
            )
            if o["status"] == "shipped" and o["tracking_code"]:
                txt += f"   📦 کد رهگیری: {o['tracking_code']}\n"

    await message.reply(txt)

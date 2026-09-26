from utils.date_utils import to_jalali
from bale import MenuKeyboardMarkup, MenuKeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def main_kb(is_admin=False, is_staff=False, is_warehouse=False, has_installment=False, is_finance=False):
    kb = MenuKeyboardMarkup()
    kb.add(MenuKeyboardButton("ثبت سفارش جدید"),  row=1)
    kb.add(MenuKeyboardButton("حساب کاربری"),      row=1)
    kb.add(MenuKeyboardButton("اخبار و اطلاعیه"),  row=2)
    kb.add(MenuKeyboardButton("روزنامه"),           row=2)
    kb.add(MenuKeyboardButton("کاتالوگ و اطلاعات"),row=3)
    kb.add(MenuKeyboardButton("سوالات متداول"),     row=3)
    kb.add(MenuKeyboardButton("پشتیبانی"),          row=4)
    kb.add(MenuKeyboardButton("ارتباط با ما"),      row=4)
    kb.add(MenuKeyboardButton("درباره ما"),          row=5)
    next_row = 6
    if has_installment:
        kb.add(MenuKeyboardButton("پرداخت اقساط"), row=next_row)
        next_row += 1
    if is_finance:
        kb.add(MenuKeyboardButton("پنل مالی"), row=next_row)
        next_row += 1
    if is_staff or is_warehouse:
        kb.add(MenuKeyboardButton("پنل کارکنان"), row=next_row)
        next_row += 1
    if is_admin:
        kb.add(MenuKeyboardButton("پنل ادمین"), row=next_row)
    return kb

def finance_panel_keyboard():
    """پنل اختصاصی مسئول مالی"""
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("فیش‌های در انتظار",   callback_data="admin_pending"),       row=1)
    kb.add(InlineKeyboardButton("اقساط در انتظار",     callback_data="admin_installments"),  row=2)
    kb.add(InlineKeyboardButton("چک‌های در انتظار",    callback_data="admin_check_docs"),    row=3)
    kb.add(InlineKeyboardButton("گزارش دوره‌ای",       callback_data="admin_report"),        row=4)
    kb.add(InlineKeyboardButton("خروجی اکسل مشتریان", callback_data="excel_customers"),     row=5)
    kb.add(InlineKeyboardButton("همه سفارش‌ها",        callback_data="admin_all_orders"),    row=6)
    return kb

def phone_request_keyboard():
    kb = MenuKeyboardMarkup()
    kb.add(MenuKeyboardButton("ارسال شماره تلفن", request_contact=True), row=0)
    return kb

def join_channel_keyboard(channel_url):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("عضویت در کانال", url=channel_url), row=1)
    kb.add(InlineKeyboardButton("عضو شدم",        callback_data="cb_joined"), row=2)
    return kb

def role_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("جراح دندانپزشک",   callback_data="cb_role_surgeon"),   row=1)
    kb.add(InlineKeyboardButton("دستیار دندانپزشک", callback_data="cb_role_assistant"), row=2)
    kb.add(InlineKeyboardButton("منشی",             callback_data="cb_role_secretary"), row=3)
    kb.add(InlineKeyboardButton("نماینده",          callback_data="cb_role_sales"),     row=4)
    kb.add(InlineKeyboardButton("سایر",             callback_data="cb_role_other"),     row=5)
    return kb

def role_confirm_keyboard(role_text):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ بله، مطمئنم", callback_data=f"cb_role_confirm"), row=1)
    kb.add(InlineKeyboardButton("❌ خیر، تغییر دهم", callback_data="cb_role_change"),  row=2)
    return kb

# ── ثبت سفارش ──
def order_category_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("پودر استخوان (X Bone)", callback_data="cb_cat_xbone"),  row=1)
    kb.add(InlineKeyboardButton("ممبران (X Patch)",      callback_data="cb_cat_xpatch"), row=2)
    return kb

def xpatch_type_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("X Patch",              callback_data="cb_sub_xpatch"),    row=1)
    kb.add(InlineKeyboardButton("Cross Linked X Patch", callback_data="cb_sub_crosslinked"), row=2)
    kb.add(InlineKeyboardButton("بازگشت",               callback_data="cb_order_back"),    row=3)
    return kb

def particle_size_keyboard(sizes):
    kb = InlineKeyboardMarkup()
    for i, s in enumerate(sizes):
        kb.add(InlineKeyboardButton(s, callback_data=f"cb_particle_{i}"), row=i+1)
    kb.add(InlineKeyboardButton("بازگشت", callback_data="cb_order_back"), row=len(sizes)+1)
    return kb

def volume_size_keyboard(products):
    kb = InlineKeyboardMarkup()
    for i, p in enumerate(products):
        stock_txt = f" (موجودی: {p['stock']})" if p['stock'] > 0 else " (ناموجود)"
        kb.add(InlineKeyboardButton(
            f"{p['volume_size']}{stock_txt}",
            callback_data=f"cb_vol_{p['id']}"
        ), row=i+1)
    kb.add(InlineKeyboardButton("بازگشت", callback_data="cb_order_back"), row=len(products)+1)
    return kb

def cart_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("افزودن محصول دیگر", callback_data="cb_add_more"),      row=1)
    kb.add(InlineKeyboardButton("تایید سفارش",       callback_data="cb_confirm_order"), row=2)
    kb.add(InlineKeyboardButton("لغو",               callback_data="cb_cancel_order"),  row=3)
    return kb

def invoice_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("تایید نهایی و پرداخت", callback_data="cb_final_confirm"), row=1)
    kb.add(InlineKeyboardButton("لغو",                  callback_data="cb_cancel_order"),  row=2)
    return kb

def receipt_admin_keyboard(order_num):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("تایید پرداخت", callback_data=f"approve_{order_num}"), row=1)
    kb.add(InlineKeyboardButton("رد پرداخت",    callback_data=f"reject_{order_num}"),  row=2)
    return kb

# ── FAQ ──
def faq_keyboard(faqs):
    kb = InlineKeyboardMarkup()
    for i, f in enumerate(faqs):
        kb.add(InlineKeyboardButton(f["question"][:40], callback_data=f"cb_faq_{f['id']}"), row=i)
    return kb

# ── پشتیبانی ──
def support_subject_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("مالی",   callback_data="cb_sup_financial"), row=1)
    kb.add(InlineKeyboardButton("کیفیت",  callback_data="cb_sup_quality"),   row=2)
    kb.add(InlineKeyboardButton("ارسال",  callback_data="cb_sup_shipping"),  row=3)
    kb.add(InlineKeyboardButton("سایر",   callback_data="cb_sup_other"),     row=3)
    return kb

# ── پنل ادمین ──
def admin_main_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("فیش‌های در انتظار",  callback_data="admin_pending"),      row=1)
    kb.add(InlineKeyboardButton("همه سفارش‌ها",       callback_data="admin_all_orders"),   row=1)
    kb.add(InlineKeyboardButton("مدیریت کاربران",     callback_data="admin_users"),        row=2)
    kb.add(InlineKeyboardButton("موجودی انبار",       callback_data="admin_stock"),        row=2)
    kb.add(InlineKeyboardButton("محصولات",            callback_data="admin_products"),     row=3)
    kb.add(InlineKeyboardButton("تخفیف‌ها",           callback_data="admin_discounts"),    row=3)
    kb.add(InlineKeyboardButton("مدیریت کارکنان",     callback_data="admin_staff_mgmt"),   row=4)
    kb.add(InlineKeyboardButton("گزارش کارکنان",      callback_data="admin_reports"),      row=4)
    kb.add(InlineKeyboardButton("تیکت‌های پشتیبانی",  callback_data="admin_tickets"),      row=5)
    kb.add(InlineKeyboardButton("سوالات متداول",      callback_data="admin_faq"),          row=5)
    kb.add(InlineKeyboardButton("اطلاعیه جدید",          callback_data="admin_news_add"),      row=6)
    kb.add(InlineKeyboardButton("اطلاعیه کارکنان",      callback_data="admin_staff_news"),    row=6)
    kb.add(InlineKeyboardButton("روزنامه",               callback_data="admin_newspaper"),     row=7)
    kb.add(InlineKeyboardButton("کاتالوگ و اطلاعات", callback_data="admin_catalog_mgmt"), row=7)
    kb.add(InlineKeyboardButton("اقساط در انتظار",    callback_data="admin_installments"), row=8)
    kb.add(InlineKeyboardButton("چک‌های در انتظار",     callback_data="admin_check_docs"),    row=8)
    kb.add(InlineKeyboardButton("سفارشات تکمیل شده", callback_data="admin_completed"),    row=9)
    kb.add(InlineKeyboardButton("سفارشات در جریان",   callback_data="admin_inprogress"),   row=9)
    kb.add(InlineKeyboardButton("گزارش دوره‌ای",      callback_data="admin_report"),       row=10)
    kb.add(InlineKeyboardButton("خروجی اکسل مشتریان",callback_data="excel_customers"),    row=10)
    kb.add(InlineKeyboardButton("پیام همگانی",        callback_data="admin_broadcast"),    row=11)
    kb.add(InlineKeyboardButton("تنظیمات",            callback_data="admin_settings"),     row=11)
    return kb

def admin_settings_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("شماره کارت",     callback_data="admin_set_bank_card"),  row=1)
    kb.add(InlineKeyboardButton("نام صاحب حساب",  callback_data="admin_set_bank_owner"), row=1)
    kb.add(InlineKeyboardButton("آیدی کانال",     callback_data="admin_set_channel"),    row=2)
    kb.add(InlineKeyboardButton("لینک کانال",     callback_data="admin_set_channel_url"),row=2)
    kb.add(InlineKeyboardButton("عضویت اجباری",   callback_data="admin_toggle_channel"), row=3)
    kb.add(InlineKeyboardButton("متن خوشامدگویی", callback_data="admin_set_welcome"),    row=3)
    kb.add(InlineKeyboardButton("متن پرداخت",     callback_data="admin_set_payment"),    row=4)
    kb.add(InlineKeyboardButton("متن تماس با ما", callback_data="admin_set_contact"),    row=4)
    kb.add(InlineKeyboardButton("متن درباره ما",  callback_data="admin_set_about"),      row=5)
    kb.add(InlineKeyboardButton("متن تعهدنامه",   callback_data="admin_set_commitment"), row=6)
    kb.add(InlineKeyboardButton("بازگشت",         callback_data="admin_back_main"),      row=6)
    return kb

def admin_products_keyboard(prods):
    kb = InlineKeyboardMarkup()
    row = 1
    kb.add(InlineKeyboardButton("افزودن محصول جدید", callback_data="admin_prod_add"), row=row); row+=1
    for p in prods:
        label = f"{p['catalog_code']} | {p['volume_size']} | {p['particle_size']}"
        kb.add(InlineKeyboardButton(label[:45], callback_data=f"admin_prod_{p['id']}"), row=row)
        row += 1
    kb.add(InlineKeyboardButton("بازگشت", callback_data="admin_back_main"), row=row)
    return kb

def admin_product_detail_keyboard(pid, is_active):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("ویرایش قیمت",   callback_data=f"admin_prod_price_{pid}"),  row=1)
    kb.add(InlineKeyboardButton("ویرایش موجودی", callback_data=f"admin_prod_stock_{pid}"),  row=2)
    kb.add(InlineKeyboardButton("🗑️ حذف محصول", callback_data=f"admin_prod_delete_{pid}"), row=3)
    kb.add(InlineKeyboardButton("بازگشت",         callback_data="admin_products"),           row=4)
    return kb

def staff_list_keyboard(staff_list):
    seen = {}
    for s in staff_list:
        bid = s["bale_id"]
        if bid not in seen: seen[bid] = s["full_name"] or str(bid)
    kb = InlineKeyboardMarkup()
    for i, (bid, name) in enumerate(seen.items()):
        kb.add(InlineKeyboardButton(name, callback_data=f"admin_staff_edit_{bid}"), row=i)
    r = len(seen)
    kb.add(InlineKeyboardButton("افزودن کارمند", callback_data="admin_staff_add"),  row=r)
    kb.add(InlineKeyboardButton("بازگشت",        callback_data="admin_back_main"), row=r+1)
    return kb

def staff_roles_keyboard(target_id, current_roles):
    from database.db import STAFF_ROLES
    kb = InlineKeyboardMarkup()
    for i, (rkey, rname) in enumerate(STAFF_ROLES.items()):
        check = "✓" if rkey in current_roles else "○"
        kb.add(InlineKeyboardButton(f"{check} {rname}", callback_data=f"admin_staff_toggle_{target_id}_{rkey}"), row=i)
    r = len(STAFF_ROLES)
    kb.add(InlineKeyboardButton("ارسال تسک",   callback_data=f"admin_staff_task_{target_id}"),  row=r)
    kb.add(InlineKeyboardButton("لیست تسک‌ها", callback_data=f"admin_task_list_{target_id}"),   row=r)
    kb.add(InlineKeyboardButton("حذف کامل",    callback_data=f"admin_staff_remove_{target_id}"), row=r+1)
    kb.add(InlineKeyboardButton("بازگشت",      callback_data="admin_staff_mgmt"),                row=r+2)
    return kb

def admin_discounts_keyboard(discounts):
    ROLES = ["🔬 جراح دندانپزشک","🩺 دستیار دندانپزشک","📋 منشی","🤝 نماینده"]
    dm = {d["role"]: d for d in discounts}
    kb = InlineKeyboardMarkup()
    for i, role in enumerate(ROLES):
        d = dm.get(role)
        val = f"{d['discount_value']}%" if d and d["discount_type"]=="percent" else (f"{d['discount_value']:,}ت" if d else "بدون تخفیف")
        kb.add(InlineKeyboardButton(f"{role}: {val}", callback_data=f"admin_disc_edit_{i}"), row=i)
    kb.add(InlineKeyboardButton("بازگشت", callback_data="admin_back_main"), row=len(ROLES))
    return kb

def warehouse_main_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("سفارش‌های آماده ارسال", callback_data="wh_ready_orders"), row=1)
    kb.add(InlineKeyboardButton("مدیریت موجودی",         callback_data="wh_stock"),        row=2)
    kb.add(InlineKeyboardButton("منوی اصلی",             callback_data="wh_back"),          row=3)
    return kb

def catalog_manage_keyboard(items):
    kb = InlineKeyboardMarkup()
    for i, item in enumerate(items):
        icon = "فیلم" if item["item_type"] in ("video","file") else "فایل"
        kb.add(InlineKeyboardButton(f"حذف | {icon} {item['title'][:20]}", callback_data=f"admin_catalog_del_{item['id']}"), row=i)
    r = len(items)
    kb.add(InlineKeyboardButton("افزودن لینک/PDF",  callback_data="admin_catalog_add_url"),  row=r)
    kb.add(InlineKeyboardButton("افزودن فایل/ویدیو", callback_data="admin_catalog_add_file"), row=r+1)
    kb.add(InlineKeyboardButton("بازگشت",            callback_data="admin_back_main"),        row=r+2)
    return kb

def admin_tickets_keyboard(tickets):
    kb = InlineKeyboardMarkup()
    for i, t in enumerate(tickets[:10]):
        s = "باز" if t["status"]=="open" else "پاسخ داده شده"
        kb.add(InlineKeyboardButton(f"{t['ticket_code']} | {t['full_name'][:8]} | {s}", callback_data=f"admin_ticket_{t['id']}"), row=i)
    kb.add(InlineKeyboardButton("بازگشت", callback_data="admin_back_main"), row=len(tickets[:10]))
    return kb

def admin_faq_keyboard(faqs):
    kb = InlineKeyboardMarkup()
    for i, f in enumerate(faqs):
        kb.add(InlineKeyboardButton(f"حذف | {f['question'][:30]}", callback_data=f"admin_faq_del_{f['id']}"), row=i)
    r = len(faqs)
    kb.add(InlineKeyboardButton("افزودن سوال جدید", callback_data="admin_faq_add"), row=r)
    kb.add(InlineKeyboardButton("بازگشت",           callback_data="admin_back_main"), row=r+1)
    return kb

def admin_newspaper_keyboard(items):
    kb = InlineKeyboardMarkup()
    for i, n in enumerate(items):
        kb.add(InlineKeyboardButton(f"حذف | {n['title'][:25]}", callback_data=f"admin_np_del_{n['id']}"), row=i)
    r = len(items)
    kb.add(InlineKeyboardButton("افزودن شماره جدید", callback_data="admin_np_add"), row=r)
    kb.add(InlineKeyboardButton("بازگشت",            callback_data="admin_back_main"), row=r+1)
    return kb

def staff_reporters_keyboard(reporters):
    kb = InlineKeyboardMarkup()
    for i, r in enumerate(reporters):
        kb.add(InlineKeyboardButton(f"{r['full_name']} ({r['report_count']} گزارش)", callback_data=f"admin_rep_user_{r['bale_id']}"), row=i)
    kb.add(InlineKeyboardButton("بازگشت", callback_data="admin_back_main"), row=len(reporters))
    return kb

def staff_report_list_keyboard(reports, bale_id):
    kb = InlineKeyboardMarkup()
    for i, r in enumerate(reports[:10]):
        kb.add(InlineKeyboardButton(f"{to_jalali(r['created_at'])} — {(r['report_text'] or '')[:15]}", callback_data=f"admin_rep_detail_{r['id']}"), row=i)
    kb.add(InlineKeyboardButton("بازگشت", callback_data="admin_reports"), row=len(reports[:10]))
    return kb

# ── نوع پرداخت ───────────────────────────────────────────
def payment_type_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("پرداخت کامل",                    callback_data="cb_pay_full"),         row=1)
    kb.add(InlineKeyboardButton("پرداخت اقساطی (۵۰٪ پیش‌پرداخت)", callback_data="cb_pay_installment"),  row=2)
    kb.add(InlineKeyboardButton("اقساطی بدون پیش‌پرداخت",         callback_data="cb_pay_inst_zero"),    row=3)
    kb.add(InlineKeyboardButton("چک / تعهدنامه",                  callback_data="cb_pay_check"),        row=4)
    kb.add(InlineKeyboardButton("بازگشت",                         callback_data="cb_order_back"),       row=5)
    return kb

def check_confirm_keyboard():
    """تأیید تعهدنامه"""
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ تأیید کردم و متعهد هستم", callback_data="cb_check_confirm"), row=1)
    kb.add(InlineKeyboardButton("بازگشت",                     callback_data="cb_pay_back"),      row=2)
    return kb

def finance_check_keyboard(order_num):
    """دکمه‌های مالی برای چک/تعهدنامه"""
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ تأیید بدون چک",      callback_data=f"fin_approve_{order_num}"),      row=1)
    kb.add(InlineKeyboardButton("📄 نیاز به چک/سفته",   callback_data=f"fin_need_check_{order_num}"),   row=2)
    kb.add(InlineKeyboardButton("❌ رد درخواست",         callback_data=f"fin_reject_{order_num}"),       row=3)
    return kb

def finance_check_final_keyboard(order_num):
    """دکمه‌های مالی بعد از دریافت چک"""
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ تأیید نهایی",  callback_data=f"fin_final_{order_num}"),  row=1)
    kb.add(InlineKeyboardButton("❌ رد",           callback_data=f"fin_reject_{order_num}"), row=2)
    return kb

def installment_approve_keyboard(payment_id, order_num):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("تایید پرداخت قسط", callback_data=f"inst_approve_{payment_id}_{order_num}"), row=1)
    kb.add(InlineKeyboardButton("رد",               callback_data=f"inst_reject_{payment_id}"),              row=2)
    return kb

def report_period_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("۱ ماه گذشته",  callback_data="rep_30"),  row=1)
    kb.add(InlineKeyboardButton("۳ ماه گذشته",  callback_data="rep_90"),  row=2)
    kb.add(InlineKeyboardButton("۶ ماه گذشته",  callback_data="rep_180"), row=3)
    kb.add(InlineKeyboardButton("۱ سال گذشته",  callback_data="rep_365"), row=4)
    kb.add(InlineKeyboardButton("بازگشت",        callback_data="admin_back_main"), row=5)
    return kb

def excel_period_keyboard(prefix):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("۱ ماه گذشته",  callback_data=f"{prefix}_30"),  row=1)
    kb.add(InlineKeyboardButton("۳ ماه گذشته",  callback_data=f"{prefix}_90"),  row=2)
    kb.add(InlineKeyboardButton("۶ ماه گذشته",  callback_data=f"{prefix}_180"), row=3)
    kb.add(InlineKeyboardButton("۱ سال گذشته",  callback_data=f"{prefix}_365"), row=4)
    kb.add(InlineKeyboardButton("بازگشت",        callback_data="admin_back_main"), row=5)
    return kb

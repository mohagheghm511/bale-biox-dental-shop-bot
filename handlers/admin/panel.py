from utils.date_utils import to_jalali, now_jalali, today_jalali
from database.db import get_check_doc, update_check_doc, get_pending_check_docs, get_finance_staff
from bale import InputFile
import json
from database.db import (
    get_setting, set_setting,
    get_all_staff, get_staff_roles, add_staff_role, remove_staff_role, remove_all_staff_roles, STAFF_ROLES,
    get_order, update_order, get_user, get_all_users, ban_user,
    get_orders_by_status, get_all_orders, get_all_products, get_product,
    update_product, add_product, delete_product,
    get_all_staff_reporters, get_staff_reports_by_user, get_report_detail,
    add_news, delete_news, get_news,
    get_catalog_items, add_catalog_item, delete_catalog_item,
    get_faqs, get_faq, add_faq, delete_faq,
    get_newspaper, add_newspaper, delete_newspaper,
    get_ticket_by_id, get_open_tickets, get_all_tickets, update_ticket,
    get_all_discounts, set_discount, delete_discount,
    get_state, set_state, clear_state, upsert_user,
    get_all_installments, get_all_attendance_reporters, get_staff_attendance_reports,
    add_staff_news, get_staff_news, delete_staff_news,
    add_task, get_user_tasks
)

from utils.keyboards import (
    admin_faq_keyboard, admin_newspaper_keyboard,
    admin_tickets_keyboard,
    admin_main_keyboard, admin_settings_keyboard, admin_products_keyboard,
    admin_product_detail_keyboard, staff_roles_keyboard, staff_list_keyboard,
    catalog_manage_keyboard, receipt_admin_keyboard, main_kb,
    admin_discounts_keyboard, admin_tickets_keyboard,
    staff_reporters_keyboard, staff_report_list_keyboard
)

ROLES_LIST = ["🔬 جراح دندانپزشک", "🩺 دستیار دندانپزشک", "📋 منشی", "🤝 نماینده"]


def is_super_admin(bale_id):
    from bot import SUPER_ADMIN_IDS
    return bale_id in SUPER_ADMIN_IDS

def _back_keyboard(bale_id):
    """کیبورد بازگشت مناسب برای ادمین یا مالی"""
    from database.db import has_staff_role
    if is_super_admin(bale_id):
        from utils.keyboards import admin_main_keyboard
        return admin_main_keyboard()
    elif has_staff_role(bale_id, "finance"):
        from utils.keyboards import finance_panel_keyboard
        return finance_panel_keyboard()
    return None


async def cmd_admin_panel(bot, message):
    bale_id = int(message.author.user_id)
    if not is_super_admin(bale_id):
        await message.reply("⛔ دسترسی ندارید.")
        return
    await _show_dashboard(bot, bale_id, message, send_new=True)


async def _show_dashboard(bot, bale_id, message, send_new=False):
    pending = get_orders_by_status("receipt_sent")
    open_tickets = get_open_tickets()
    users = get_all_users(500)
    text = (
        f"⚙️ *پنل مدیریت BioX*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📩 فیش در انتظار: {len(pending)}\n"
        f"🎫 تیکت‌های باز: {len(open_tickets)}\n"
        f"👥 کل کاربران: {len(users)}\n"
    )
    if send_new:
        await message.reply(text, components=_back_keyboard(bale_id))
    else:
        await message.edit(text, components=_back_keyboard(bale_id))


# ══ روتر اصلی ══════════════════════════════════════════
async def route_admin_callback(bot, callback):
    bale_id = int(callback.from_user.user_id)
    data = callback.data
    from database.db import has_staff_role

    # مسئول مالی فقط به بخش‌های مالی دسترسی داره
    is_finance = has_staff_role(bale_id, "finance")

    if not is_super_admin(bale_id):
        # بررسی دسترسی مالی
        finance_ok = False
        if is_finance:
            finance_prefixes = [
                "admin_pending", "admin_all_orders", "admin_installments",
                "admin_check_docs", "admin_check_detail_", "admin_report",
                "admin_back_main", "fin_approve_", "fin_need_check_",
                "fin_reject_", "fin_final_", "excel_customers",
                "excel_orders_", "rep_", "approve_", "reject_",
                "inst_approve_", "inst_reject_"
            ]
            for prefix in finance_prefixes:
                if data.startswith(prefix) or data == prefix:
                    finance_ok = True
                    break
        if not finance_ok:
            await callback.message.edit("⛔ دسترسی ندارید.")
            return

    if data == "admin_back_main":
        from database.db import has_staff_role
        if is_super_admin(bale_id):
            await _show_dashboard(bot, bale_id, callback.message)
        elif has_staff_role(bale_id, "finance"):
            from utils.keyboards import finance_panel_keyboard
            await callback.message.edit("پنل مالی:", components=finance_panel_keyboard())
        else:
            await callback.message.edit("بازگشت به منو.")

    elif data == "admin_pending":
        await _show_pending(bot, callback)

    elif data == "admin_all_orders":
        await _show_all_orders(bot, callback)

    elif data == "admin_users":
        await _show_users(bot, callback)

    elif data.startswith("admin_user_ban_"):
        uid = int(data.replace("admin_user_ban_", ""))
        user = get_user(uid)
        new_val = 0 if user["is_banned"] else 1
        ban_user(uid, new_val)
        status = "🚫 مسدود شد" if new_val else "✅ رفع مسدودی شد"
        await callback.message.edit(f"{status}: {user['full_name']}", components=_back_keyboard(bale_id))

    elif data == "admin_stock":
        await _show_stock(bot, callback)

    elif data == "admin_products":
        prods = get_all_products()
        await callback.message.edit("🛍 *مدیریت محصولات:*", components=admin_products_keyboard(prods))

    elif data.startswith("admin_prod_"):
        await _handle_product(bot, callback, bale_id, data)

    elif data == "admin_discounts":
        discounts = get_all_discounts()
        await callback.message.edit(
            "🎯 *مدیریت تخفیف‌ها:*\n"
            "برای ویرایش روی هر نقش کلیک کنید:",
            components=admin_discounts_keyboard(discounts)
        )

    elif data.startswith("admin_disc_edit_"):
        idx = int(data.replace("admin_disc_edit_", ""))
        role = ROLES_LIST[idx]
        set_state(bale_id, "A_DISCOUNT_VAL", {"role": role, "role_idx": idx})
        await callback.message.edit(
            f"🎯 تخفیف برای *{role}*\n\n"
            f"مقدار تخفیف را وارد کنید:\n"
            f"• برای درصد: عدد + % مثلاً: `10%`\n"
            f"• برای مبلغ ثابت: فقط عدد مثلاً: `500000`\n"
            f"• برای حذف تخفیف: `0`"
        )

    elif data == "admin_staff_mgmt":
        await _show_staff_list(bot, callback)

    elif data == "admin_staff_add":
        set_state(bale_id, "A_ADD_STAFF_ID")
        await callback.message.edit("👔 آیدی عددی بله کارمند جدید را وارد کنید:")

    elif data.startswith("admin_staff_edit_"):
        target_id = int(data.replace("admin_staff_edit_", ""))
        current_roles = get_staff_roles(target_id)
        user = get_user(target_id)
        name = user["full_name"] if user else str(target_id)
        user_role = user["role"] if user and user["role"] else "-"
        roles_text = ", ".join(STAFF_ROLES[r] for r in current_roles) if current_roles else "ندارد"
        await callback.message.edit(
            f"👤 {name}\n"
            f"سمت ثبت‌نامی: {user_role}\n"
            f"نقش در سیستم: {roles_text}\n\n"
            f"نقش‌ها را انتخاب/حذف کنید:",
            components=staff_roles_keyboard(target_id, current_roles)
        )

    elif data.startswith("admin_staff_toggle_"):
        parts = data.replace("admin_staff_toggle_", "").split("_", 1)
        target_id = int(parts[0])
        role_key = parts[1]
        current = get_staff_roles(target_id)
        if role_key in current:
            remove_staff_role(target_id, role_key)
        else:
            add_staff_role(target_id, role_key, added_by=bale_id)
        current_roles = get_staff_roles(target_id)
        user = get_user(target_id)
        name = user["full_name"] if user else str(target_id)
        roles_text = ", ".join(STAFF_ROLES[r] for r in current_roles) if current_roles else "ندارد"
        user_role = user["role"] if user and user["role"] else "-"
        await callback.message.edit(
            f"👤 {name}\n"
            f"سمت ثبت‌نامی: {user_role}\n"
            f"نقش در سیستم: {roles_text}\n\n"
            f"نقش‌ها را انتخاب/حذف کنید:",
            components=staff_roles_keyboard(target_id, current_roles)
        )

    elif data.startswith("admin_staff_remove_"):
        target_id = int(data.replace("admin_staff_remove_", ""))
        remove_all_staff_roles(target_id)
        await callback.message.edit("✅ تمام دسترسی‌های کارمند حذف شد.", components=_back_keyboard(bale_id))

    elif data.startswith("admin_staff_task_"):
        target_id = int(data.replace("admin_staff_task_", ""))
        user = get_user(target_id)
        name = user["full_name"] if user else str(target_id)
        set_state(bale_id, "A_TASK_TITLE", {"task_target": target_id, "task_target_name": name})
        await callback.message.edit(f"ارسال تسک برای {name}\n\nعنوان تسک را بنویسید:")

    elif data.startswith("admin_task_list_"):
        target_id = int(data.replace("admin_task_list_", ""))
        from database.db import get_user_tasks
        tasks = get_user_tasks(target_id)
        user = get_user(target_id)
        name = user["full_name"] if user else str(target_id)
        if not tasks:
            await callback.message.edit(f"تسکی برای {name} ثبت نشده.", components=_back_keyboard(bale_id))
            return
        txt = f"تسک‌های {name}:\n━━━━━━━━━━━━━━━\n"
        for t in tasks[:10]:
            status = "✅" if t["status"] == "done" else "📋"
            txt += f"{status} {t['title']} | {to_jalali(t['created_at'])}\n"
        await callback.message.edit(txt, components=_back_keyboard(bale_id))

    elif data == "admin_reports":
        reporters = get_all_staff_reporters()
        if not reporters:
            await callback.message.edit("📊 هیچ گزارشی ثبت نشده.", components=_back_keyboard(bale_id))
            return
        await callback.message.edit(
            "📊 *گزارش کارکنان:*\nیک کارمند را انتخاب کنید:",
            components=staff_reporters_keyboard(reporters)
        )

    elif data.startswith("admin_rep_user_"):
        target_id = int(data.replace("admin_rep_user_", ""))
        reports = get_staff_reports_by_user(target_id, 20)
        user = get_user(target_id)
        name = user["full_name"] if user else str(target_id)
        if not reports:
            await callback.message.edit(f"📋 {name} گزارشی ثبت نکرده.", components=_back_keyboard(bale_id))
            return
        await callback.message.edit(
            f"📋 *گزارش‌های {name}:*\n(جدیدترین اول)",
            components=staff_report_list_keyboard(reports, target_id)
        )

    elif data.startswith("admin_rep_detail_"):
        rid = int(data.replace("admin_rep_detail_", ""))
        r = get_report_detail(rid)
        if not r:
            return
        # بررسی ورود/خروج همان روز
        date = r["created_at"][:10]
        from database.db import get_conn as _gc
        conn = _gc()
        att = conn.execute(
            "SELECT * FROM attendances WHERE bale_id=? AND date=? ORDER BY id DESC LIMIT 1",
            (r["bale_id"], date)
        ).fetchone()
        conn.close()

        att_txt = ""
        if att:
            hrs = att["total_minutes"] // 60
            mns = att["total_minutes"] % 60
            clock_in_t  = att["clock_in"][:5]  if att["clock_in"]  else "---"
            clock_out_t = att["clock_out"][:5] if att["clock_out"] else "هنوز خروج نزده"
            att_txt = (
                f"\n⏰ ورود: {clock_in_t} | خروج: {clock_out_t}\n"
                f"⏱ مجموع کار: {hrs} ساعت و {mns} دقیقه\n"
            )

        txt = (
            f"جزئیات گزارش\n"
            f"━━━━━━━━━━━━━━━\n"
            f"تاریخ: {to_jalali(r['created_at'], show_time=True)}\n"
            f"نوع: {r['report_type']}"
            f"{att_txt}"
            f"━━━━━━━━━━━━━━━\n"
            f"{r['report_text'] or '-'}"
        )
        if r["file_id"] and r["file_type"] == "photo":
            await bot.send_photo(bale_id, InputFile(r["file_id"]), caption=txt)
        elif r["file_id"] and r["file_type"] == "document":
            await bot.send_document(bale_id, InputFile(r["file_id"]), caption=txt)
        else:
            await callback.message.edit(txt, components=_back_keyboard(bale_id))

    elif data == "admin_tickets":
        tickets = get_open_tickets() or get_all_tickets(20)
        if not tickets:
            await callback.message.edit("تیکتی وجود ندارد.", components=_back_keyboard(bale_id)); return
        await callback.message.edit(f"تیکت2019های پشتیبانی:", components=admin_tickets_keyboard(tickets))
        tickets = get_open_tickets()
        if not tickets:
            all_t = get_all_tickets(10)
            if not all_t:
                await callback.message.edit("🎫 هیچ تیکتی وجود ندارد.", components=_back_keyboard(bale_id))
                return
            tickets = all_t
        await callback.message.edit(
            f"💬 *تیکت‌ها ({len(tickets)}):*",
            components=admin_tickets_keyboard(tickets)
        )

    elif data.startswith("admin_ticket_"):
        if data.startswith("admin_ticket_reply_"):
            code = data.replace("admin_ticket_reply_", "")
            ticket = get_ticket(code)
            if not ticket:
                return
            set_state(bale_id, "A_TICKET_REPLY", {"ticket_id": ticket["id"], "ticket_code": code, "user_bale_id": ticket["bale_id"]})
            await callback.message.edit(
                f"💬 پاسخ به تیکت *{code}*:\n\nمتن پاسخ را بنویسید:"
            )
        else:
            tid = int(data.replace("admin_ticket_", ""))
            ticket = get_ticket_by_id(tid)
            if not ticket:
                return
            set_state(bale_id, "A_TICKET_REPLY", {"ticket_id": tid, "ticket_code": ticket["ticket_code"], "user_bale_id": ticket["bale_id"]})
            user = get_user(ticket["bale_id"])
            txt = (
                f"🎫 *تیکت {ticket['ticket_code']}*\n"
                f"━━━━━━━━━━━━━━━\n"
                f"👤 {user['full_name'] if user else '-'}\n"
                f"📌 موضوع: {ticket['subject']}\n"
                f"📅 {to_jalali(ticket['created_at'])}\n"
                f"💬 پیام: {ticket['message_text'] or '[فایل پیوست]'}\n\n"
                f"━━━━━━━━━━━━━━━\n"
                f"متن پاسخ را بنویسید:"
            )
            await callback.message.edit(txt)

    elif data == "admin_faq":
        await _show_faq(bot, callback)

    elif data == "admin_faq_add":
        set_state(bale_id, "A_FAQ_Q")
        await callback.message.edit("سوال جدید را بنویسید:")

    elif data.startswith("admin_faq_del_"):
        fid = int(data.replace("admin_faq_del_", ""))
        delete_faq(fid)
        await callback.message.edit("سوال حذف شد.", components=admin_faq_keyboard(get_faqs()))

    elif data == "admin_newspaper":
        await _show_newspaper(bot, callback)

    elif data == "admin_np_add":
        set_state(bale_id, "A_NP_TITLE")
        await callback.message.edit("عنوان شماره روزنامه را وارد کنید:")

    elif data.startswith("admin_np_del_"):
        nid = int(data.replace("admin_np_del_", ""))
        delete_newspaper(nid)
        items = get_newspaper(20)
        await callback.message.edit("حذف شد.", components=admin_newspaper_keyboard(items))

    elif data.startswith("admin_ticket_"):
        await _show_ticket_detail(bot, callback, bale_id, data)

    elif data == "admin_catalog_mgmt":
        items = get_catalog_items(20)
        await callback.message.edit(
            "📂 *مدیریت کاتالوگ:*",
            components=catalog_manage_keyboard(items)
        )

    elif data == "admin_catalog_add_url":
        set_state(bale_id, "A_CATALOG_TITLE", {"catalog_type": "url"})
        await callback.message.edit("عنوان PDF/کاتالوگ را بنویسید:")

    elif data == "admin_catalog_add_file":
        set_state(bale_id, "A_CATALOG_TITLE", {"catalog_type": "file"})
        await callback.message.edit("عنوان ویدیو/فایل را بنویسید:")

    elif data.startswith("admin_catalog_del_"):
        cid = int(data.replace("admin_catalog_del_", ""))
        delete_catalog_item(cid)
        items = get_catalog_items(20)
        await callback.message.edit("✅ حذف شد.\n\n📂 *مدیریت کاتالوگ:*", components=catalog_manage_keyboard(items))

    elif data == "admin_staff_news":
        await _show_staff_news_mgmt(bot, callback, bale_id)

    elif data == "admin_staff_news_add":
        set_state(bale_id, "A_STAFF_NEWS_TITLE")
        await callback.message.edit("عنوان اطلاعیه کارکنان را بنویسید:")

    elif data.startswith("admin_staff_news_del_"):
        nid = int(data.replace("admin_staff_news_del_",""))
        delete_staff_news(nid)
        await _show_staff_news_mgmt(bot, callback, bale_id)

    elif data == "admin_news_add":
        set_state(bale_id, "A_NEWS_TITLE")
        await callback.message.edit("📰 عنوان اطلاعیه را بنویسید:")

    elif data == "admin_check_docs":
        docs = get_pending_check_docs()
        if not docs:
            await callback.message.edit("چک/تعهدنامه‌ای در انتظار نیست.", components=_back_keyboard(bale_id))
            return
        from bale import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup()
        for i, d in enumerate(docs[:10]):
            status_fa = {"pending": "در انتظار", "need_check": "نیاز به چک", "check_received": "چک دریافت شد"}.get(d["status"], d["status"])
            kb.add(InlineKeyboardButton(
                f"{d['full_name']} | {d['order_number']} | {status_fa}",
                callback_data=f"admin_check_detail_{d['order_number']}"
            ), row=i+1)
        kb.add(InlineKeyboardButton("بازگشت", callback_data="admin_back_main"), row=len(docs)+1)
        await callback.message.edit(f"چک‌های در انتظار ({len(docs)}):", components=kb)

    elif data.startswith("admin_check_detail_"):
        order_num = data.replace("admin_check_detail_","")
        doc = get_check_doc(order_num)
        if not doc: return
        user = get_user(doc["bale_id"])
        from bale import InputFile, InlineKeyboardMarkup, InlineKeyboardButton
        from utils.keyboards import finance_check_keyboard, finance_check_final_keyboard
        caption = (
            f"مدارک چک/تعهدنامه\n━━━━━━━━━━━━━━━\n"
            f"نام: {user['full_name'] if user else '-'}\n"
            f"موبایل: {user['phone'] if user else '-'}\n"
            f"کد ملی: {doc['national_id']}\n"
            f"سفارش: {order_num}\n"
            f"وضعیت: {doc['status']}"
        )
        if doc["check_file"]:
            kb = finance_check_final_keyboard(order_num)
            await bot.send_photo(bale_id, InputFile(doc["check_file"]), caption=caption + "\n\nچک/سفته:", components=kb)
        await bot.send_photo(bale_id, InputFile(doc["id_card_file"]), caption=caption + "\n\nکارت ملی:", components=finance_check_keyboard(order_num))

    elif data.startswith("fin_approve_"):
        order_num = data.replace("fin_approve_","")
        doc = get_check_doc(order_num)
        if not doc: return
        update_check_doc(order_num, status="approved")
        update_order(order_num, status="approved")
        # پیام به کاربر
        await bot.send_message(doc["bale_id"],
            f"✅ سفارش {order_num} تأیید شد!\n\n"
            "واحد مالی سفارش شما را بدون نیاز به چک تأیید کرد.\n"
            "سفارش شما در حال آماده‌سازی است."
        )
        # پیام به انباردار
        from database.db import get_all_staff, get_order as go
        import json
        order = go(order_num)
        user = get_user(doc["bale_id"])
        items = json.loads(order["items"])
        items_txt = "\n".join(f"• {i['catalog_code']} | {i['size']} × {i['qty']}" for i in items)
        wh_msg = (
            f"📦 سفارش آماده ارسال\n━━━━━━━━━━━━━━━\n"
            f"نام: {user['full_name']}\n"
            f"موبایل: {user['phone']}\n"
            f"آدرس: {user['address'] or '-'}\n"
            f"━━━━━━━━━━━━━━━\n{items_txt}"
        )
        all_staff = get_all_staff()
        for s in all_staff:
            if s["staff_role"] == "warehouse":
                try: await bot.send_message(s["bale_id"], wh_msg)
                except: pass
        await callback.message.edit("✅ تأیید شد. پیام به کاربر و انباردار ارسال شد.")

    elif data.startswith("fin_need_check_"):
        order_num = data.replace("fin_need_check_","")
        doc = get_check_doc(order_num)
        if not doc: return
        update_check_doc(order_num, status="need_check")
        from database.db import get_state as gs, set_state as ss
        ss(doc["bale_id"], "W_CHECK_FILE", {"order_num": order_num})
        await bot.send_message(doc["bale_id"],
            f"سفارش {order_num}\n\n"
            "واحد مالی درخواست داد که تصویر چک یا سفته را ارسال کنید.\n"
            "لطفاً تصویر را در این چت ارسال نمایید:"
        )
        await callback.message.edit("📄 پیام به کاربر ارسال شد. منتظر چک/سفته...")

    elif data.startswith("fin_reject_"):
        order_num = data.replace("fin_reject_","")
        set_state(bale_id, "A_FIN_REJECT", {"order_num": order_num})
        await callback.message.edit("دلیل رد درخواست را بنویسید:")

    elif data.startswith("fin_final_"):
        order_num = data.replace("fin_final_","")
        doc = get_check_doc(order_num)
        if not doc: return
        update_check_doc(order_num, status="approved")
        update_order(order_num, status="approved")
        await bot.send_message(doc["bale_id"],
            f"✅ مدارک شما تأیید شد!\nسفارش {order_num} در حال آماده‌سازی است."
        )
        # انباردار
        from database.db import get_all_staff, get_order as go
        import json
        order = go(order_num)
        user = get_user(doc["bale_id"])
        items = json.loads(order["items"])
        items_txt = "\n".join(f"• {i['catalog_code']} | {i['size']} × {i['qty']}" for i in items)
        wh_msg = (
            f"📦 سفارش آماده ارسال\n━━━━━━━━━━━━━━━\n"
            f"نام: {user['full_name']}\nموبایل: {user['phone']}\n"
            f"آدرس: {user['address'] or '-'}\n━━━━━━━━━━━━━━━\n{items_txt}"
        )
        all_staff = get_all_staff()
        for s in all_staff:
            if s["staff_role"] == "warehouse":
                try: await bot.send_message(s["bale_id"], wh_msg)
                except: pass
        await callback.message.edit("✅ تأیید نهایی شد.")

    elif data == "admin_installments":
        from database.db import get_pending_installment_payments, get_all_installments
        payments = get_pending_installment_payments()
        all_inst  = get_all_installments()
        txt = ""
        if payments:
            txt += f"فیش‌های قسط در انتظار ({len(payments)}):\n━━━━━━━━━━━━━━━\n"
            for p in payments:
                txt += f"• {p['order_number']} | {p['full_name']} | {p['amount']:,} ت\n"
            txt += "\n"
        if all_inst:
            txt += f"اقساط فعال ({len(all_inst)}):\n━━━━━━━━━━━━━━━\n"
            for i in all_inst:
                txt += f"• {i['order_number']} | {i['full_name']} | مانده: {i['remaining_amount']:,} ت | سررسید: {to_jalali(i['due_date'])}\n"
        if not txt:
            txt = "هیچ قسطی وجود ندارد."
        await callback.message.edit(txt[:4000], components=_back_keyboard(bale_id))

    elif data == "admin_completed":
        await _show_completed_orders(bot, callback)

    elif data == "admin_inprogress":
        await _show_inprogress_orders(bot, callback)

    elif data == "admin_report":
        from utils.keyboards import report_period_keyboard
        await callback.message.edit("بازه زمانی را انتخاب کنید:", components=report_period_keyboard())

    elif data == "admin_broadcast":
        set_state(bale_id, "A_BROADCAST")
        await callback.message.edit("📣 متن پیام همگانی را بنویسید:")

    elif data == "admin_settings":
        await callback.message.edit("⚙️ *تنظیمات ربات:*", components=admin_settings_keyboard())

    elif data == "admin_toggle_channel":
        cur = get_setting("channel_required", "1")
        new = "0" if cur == "1" else "1"
        set_setting("channel_required", new)
        status = "✅ فعال" if new == "1" else "❌ غیرفعال"
        await callback.message.edit(f"عضویت اجباری کانال: {status}", components=admin_settings_keyboard())

    elif data.startswith("admin_set_"):
        await _start_edit_setting(bot, callback, bale_id, data)


# ══ تأیید / رد فیش ════════════════════════════════════
async def cb_approve(bot, callback):
    bale_id = int(callback.from_user.user_id)
    if not is_super_admin(bale_id):
        return
    order_num = callback.data.replace("approve_", "")
    order = get_order(order_num)
    if not order or order["status"] != "receipt_sent":
        await callback.message.edit("⚠️ این فیش قبلاً بررسی شده.")
        return
    update_order(order_num, status="approved")

    items = json.loads(order["items"])
    items_txt = "\n".join(f"• {i['catalog_code']} | {i['size']} × {i['qty']}" for i in items)

    # پیام تایید به کاربر
    await bot.send_message(
        order["bale_id"],
        f"🎉 *پرداخت تأیید شد!*\n\n"
        f"📋 {order_num}\n"
        f"{items_txt}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"✅ مبلغ پرداختی: {order['final_amount']:,} تومان\n\n"
        f"سفارش شما در حال آماده‌سازی است. 🙏"
    )

    # اطلاع به انباردار
    from database.db import get_all_staff as gas
    all_staff = gas()
    warehouse_ids = [s["bale_id"] for s in all_staff if s["staff_role"] == "warehouse"]
    customer = get_user(order["bale_id"])
    wh_msg = (
        f"📦 *سفارش جدید برای ارسال*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 نام مشتری: {customer['full_name']}\n"
        f"📱 تماس: {customer['phone']}\n"
        f"🏠 آدرس: {customer['address'] or '-'}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📋 سفارش: {order_num}\n"
        f"اقلام:\n{items_txt}"
    )
    for wid in warehouse_ids:
        try:
            await bot.send_message(wid, wh_msg)
        except:
            pass

    await callback.message.edit((callback.message.content or "") + "\n\n✅ تأیید شد — انباردار مطلع شد")


async def cb_reject_start(bot, callback):
    bale_id = int(callback.from_user.user_id)
    if not is_super_admin(bale_id):
        return
    order_num = callback.data.replace("reject_", "")
    set_state(bale_id, "A_REJECT_REASON", {"order_num": order_num})
    await bot.send_message(bale_id, f"دلیل رد سفارش *{order_num}* را بنویسید:")


# ══ State های ادمین ════════════════════════════════════
async def state_reject_reason(bot, message):
    bale_id = int(message.author.user_id)
    if not is_super_admin(bale_id): return
    reason = (message.content or "").strip()
    _, d = get_state(bale_id)
    order_num = (d or {}).get("order_num")
    if not order_num: return
    update_order(order_num, status="rejected")
    clear_state(bale_id)
    order = get_order(order_num)
    await bot.send_message(
        order["bale_id"],
        f"❌ *پرداخت شما رد شد.*\n"
        f"📋 سفارش: {order_num}\n"
        f"📌 دلیل: {reason}\n\n"
        f"لطفاً با پشتیبانی تماس بگیرید."
    )
    await message.reply(f"✅ رد سفارش {order_num} ثبت شد.")


async def state_add_staff_id(bot, message):
    bale_id = int(message.author.user_id)
    if not is_super_admin(bale_id): return
    text = (message.content or "").strip()
    if not text.isdigit():
        await message.reply("❌ آیدی عددی معتبر وارد کنید:")
        return
    target_id = int(text)
    upsert_user(target_id)
    current_roles = get_staff_roles(target_id)
    user = get_user(target_id)
    name = user["full_name"] if user and user["full_name"] else str(target_id)
    clear_state(bale_id)
    await message.reply(
        f"👤 *{name}*\nنقش‌های فعلی: {', '.join(STAFF_ROLES[r] for r in current_roles) or 'ندارد'}\n\nنقش‌ها را انتخاب کنید:",
        components=staff_roles_keyboard(target_id, current_roles)
    )


async def state_ticket_reply(bot, message):
    bale_id = int(message.author.user_id)
    if not is_super_admin(bale_id): return
    text = (message.content or "").strip()
    if not text:
        await message.reply("❌ متن پاسخ خالی است:")
        return
    _, d = get_state(bale_id)
    d = d or {}
    ticket_id = d.get("ticket_id")
    ticket_code = d.get("ticket_code")
    user_bale_id = d.get("user_bale_id")
    if not ticket_id:
        return
    add_ticket_reply(ticket_id, text, from_admin=1)
    clear_state(bale_id)
    await message.reply(f"✅ پاسخ به تیکت {ticket_code} ارسال شد.")
    try:
        await bot.send_message(
            user_bale_id,
            f"📩 *پاسخ به تیکت شما*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🔢 کد: {ticket_code}\n\n"
            f"💬 {text}"
        )
    except:
        pass


async def state_discount_val(bot, message):
    bale_id = int(message.author.user_id)
    if not is_super_admin(bale_id): return
    text = (message.content or "").strip()
    _, d = get_state(bale_id)
    d = d or {}
    role = d.get("role")
    if not role:
        return
    clear_state(bale_id)
    if text == "0":
        delete_discount(role)
        await message.reply(f"✅ تخفیف {role} حذف شد.")
        return
    if text.endswith("%"):
        val = text[:-1]
        if not val.isdigit() or int(val) > 100:
            await message.reply("❌ درصد نامعتبر (مثال: 10%)")
            return
        set_discount(role, "percent", int(val))
        await message.reply(f"✅ تخفیف {role}: {val}٪")
    else:
        cleaned = text.replace(",", "").replace("،", "")
        if not cleaned.isdigit():
            await message.reply("❌ مبلغ نامعتبر (مثال: 500000)")
            return
        set_discount(role, "amount", int(cleaned))
        await message.reply(f"✅ تخفیف {role}: {int(cleaned):,} تومان")


async def state_news_title(bot, message):
    bale_id = int(message.author.user_id)
    if not is_super_admin(bale_id): return
    title = (message.content or "").strip()
    set_state(bale_id, "A_NEWS_BODY", {"news_title": title})
    await message.reply(f"عنوان: *{title}*\n\nمتن اطلاعیه را بنویسید:")


async def state_news_body(bot, message):
    bale_id = int(message.author.user_id)
    if not is_super_admin(bale_id): return
    body = (message.content or "").strip()
    _, d = get_state(bale_id)
    title = (d or {}).get("news_title", "")
    add_news(title, body)
    clear_state(bale_id)
    await message.reply(f"✅ اطلاعیه *{title}* منتشر شد.")


async def state_broadcast(bot, message):
    bale_id = int(message.author.user_id)
    if not is_super_admin(bale_id): return
    text = (message.content or "").strip()
    clear_state(bale_id)
    users = get_all_users(1000)
    sent, failed = 0, 0
    for u in users:
        try:
            await bot.send_message(u["bale_id"], f"📣 *اطلاعیه*\n\n{text}")
            sent += 1
        except:
            failed += 1
    await message.reply(f"📣 پیام همگانی ارسال شد.\n✅ موفق: {sent}\n❌ ناموفق: {failed}")


async def state_edit_setting(bot, message):
    bale_id = int(message.author.user_id)
    if not is_super_admin(bale_id): return
    text = (message.content or "").strip()
    _, d = get_state(bale_id)
    key = (d or {}).get("setting_key")
    if not key: return
    set_setting(key, text)
    clear_state(bale_id)
    await message.reply(f"✅ تنظیمات به‌روز شد.")


async def state_edit_price(bot, message):
    bale_id = int(message.author.user_id)
    if not is_super_admin(bale_id): return
    text = (message.content or "").strip().replace(",", "").replace("،", "")
    if not text.isdigit():
        await message.reply("❌ عدد صحیح وارد کنید:")
        return
    _, d = get_state(bale_id)
    update_product((d or {}).get("pid"), price=int(text))
    clear_state(bale_id)
    await message.reply(f"✅ قیمت به {int(text):,} تومان تغییر کرد.")


async def state_edit_stock(bot, message):
    bale_id = int(message.author.user_id)
    if not is_super_admin(bale_id): return
    text = (message.content or "").strip()
    if not text.isdigit():
        await message.reply("❌ عدد صحیح وارد کنید:")
        return
    _, d = get_state(bale_id)
    update_product((d or {}).get("pid"), stock=int(text))
    clear_state(bale_id)
    await message.reply(f"✅ موجودی به {text} عدد تغییر کرد.")


async def state_catalog_title(bot, message):
    bale_id = int(message.author.user_id)
    if not is_super_admin(bale_id): return
    _, d = get_state(bale_id)
    d = d or {}
    title = (message.content or "").strip()
    d["catalog_title"] = title
    ctype = d.get("catalog_type", "url")
    if ctype == "url":
        set_state(bale_id, "A_CATALOG_URL", d)
        await message.reply("لینک PDF یا صفحه وب را وارد کنید:")
    else:
        set_state(bale_id, "A_CATALOG_FILE", d)
        await message.reply("فایل یا ویدیو را ارسال کنید:")


async def state_catalog_url(bot, message):
    bale_id = int(message.author.user_id)
    if not is_super_admin(bale_id): return
    _, d = get_state(bale_id)
    d = d or {}
    url = (message.content or "").strip()
    add_catalog_item(d.get("catalog_title", ""), "url", url=url)
    clear_state(bale_id)
    await message.reply("✅ لینک به کاتالوگ اضافه شد.")


async def state_catalog_file(bot, message):
    bale_id = int(message.author.user_id)
    if not is_super_admin(bale_id): return
    _, d = get_state(bale_id)
    d = d or {}
    file_id = None
    ftype = "file"
    if hasattr(message, "document") and message.document:
        file_id = message.document.file_id
        ftype = "document"
    elif hasattr(message, "video") and message.video:
        file_id = message.video.file_id
        ftype = "video"
    elif hasattr(message, "photo") and message.photo:
        file_id = message.photo.file_id
        ftype = "photo"
    if not file_id:
        await message.reply("❌ فایل دریافت نشد. دوباره ارسال کنید.")
        return
    add_catalog_item(d.get("catalog_title", ""), ftype, file_id=file_id)
    clear_state(bale_id)
    await message.reply("✅ فایل به کاتالوگ اضافه شد.")


# ══ توابع کمکی ════════════════════════════════════════
async def _show_pending(bot, callback, bale_id=None):
    if bale_id is None: bale_id = int(callback.from_user.user_id)
    orders = get_orders_by_status("receipt_sent")
    if not orders:
        await callback.message.edit("📩 هیچ فیشی در انتظار نیست.", components=_back_keyboard(bale_id))
        return
    txt = f"📩 *فیش‌های در انتظار ({len(orders)}):*\n━━━━━━━━━━━━━━━\n"
    for o in orders:
        txt += f"• {o['order_number']} | {o['full_name']} | {o['final_amount']:,} ت\n"
    from bale import InlineKeyboardMarkup, InputFile, InlineKeyboardButton
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back_main"), row=0)
    await callback.message.edit(txt[:4000], components=kb)


async def _show_all_orders(bot, callback, bale_id=None):
    if bale_id is None: bale_id = int(callback.from_user.user_id)
    orders = get_all_orders(20)
    st = {"pending_payment": "💳", "receipt_sent": "🔍", "approved": "✅", "rejected": "❌", "shipped": "🚚"}
    txt = "📦 *آخرین ۲۰ سفارش:*\n━━━━━━━━━━━━━━━\n"
    for o in orders:
        txt += f"{st.get(o['status'], '•')} {o['order_number']} | {o['full_name']} | {o['final_amount']:,} ت\n"
        if o["tracking_code"]:
            txt += f"   📮 رهگیری: {o['tracking_code']}\n"
    await callback.message.edit(txt[:4000], components=_back_keyboard(bale_id))


async def _show_users(bot, callback):
    users = get_all_users(30)
    txt = f"👥 *کاربران ({len(users)}):*\n━━━━━━━━━━━━━━━\n"
    for u in users[:20]:
        icon = "🚫" if u["is_banned"] else "✅"
        txt += f"{icon} {u['full_name'] or 'ناشناس'} | {u['phone'] or '-'} | {u['role'] or '-'}\n"
    await callback.message.edit(txt[:4000], components=_back_keyboard(bale_id))


async def _show_stock(bot, callback):
    prods = get_all_products()
    txt = "🏭 *موجودی انبار:*\n━━━━━━━━━━━━━━━\n"
    for p in prods:
        icon = "✅" if p["stock"] > 10 else ("⚠️" if p["stock"] > 0 else "❌")
        active = "" if p["is_active"] else " [غیرفعال]"
        txt += f"{icon} {p['catalog_code']} | {p['name']}: *{p['stock']}* عدد{active}\n"
    from bale import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🛍 ویرایش محصولات", callback_data="admin_products"), row=0)
    kb.add(InlineKeyboardButton("🔙 بازگشت",         callback_data="admin_back_main"), row=1)
    await callback.message.edit(txt, components=kb)


async def _show_staff_list(bot, callback):
    staff = get_all_staff()
    if not staff:
        from bale import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("➕ افزودن کارمند", callback_data="admin_staff_add"),  row=0)
        kb.add(InlineKeyboardButton("🔙 بازگشت",        callback_data="admin_back_main"), row=1)
        await callback.message.edit("👔 هنوز کارمندی ثبت نشده.", components=kb)
        return
    await callback.message.edit(
        "👔 *لیست کارکنان:*\nبرای ویرایش نقش کلیک کنید:",
        components=staff_list_keyboard(staff)
    )


async def _handle_product(bot, callback, bale_id, data):
    if data == "admin_prod_add":
        set_state(bale_id, "A_ADD_PROD_1")
        await callback.message.edit(
            "➕ *افزودن محصول جدید*\n\n"
            "دسته‌بندی را وارد کنید:\n"
            "(xbone یا xpatch)"
        )
        return
    if data.startswith("admin_prod_price_"):
        pid = int(data.replace("admin_prod_price_", ""))
        prod = get_product(pid)
        set_state(bale_id, "A_EDIT_PRICE", {"pid": pid})
        await callback.message.edit(f"قیمت جدید *{prod['name']}* را به تومان وارد کنید:")
        return
    if data.startswith("admin_prod_stock_"):
        pid = int(data.replace("admin_prod_stock_", ""))
        prod = get_product(pid)
        set_state(bale_id, "A_EDIT_STOCK", {"pid": pid})
        await callback.message.edit(f"موجودی جدید *{prod['name']}* را وارد کنید:")
        return
    if data.startswith("admin_prod_delete_"):
        pid = int(data.replace("admin_prod_delete_", ""))
        prod = get_product(pid)
        name = prod["name"] if prod else str(pid)
        delete_product(pid)
        await callback.message.edit(
            f"🗑️ محصول «{name}» حذف شد.",
            components=admin_products_keyboard(get_all_products())
        )
        return

    if data.startswith("admin_prod_toggle_"):
        pid = int(data.replace("admin_prod_toggle_", ""))
        prod = get_product(pid)
        new_active = 0 if prod["is_active"] else 1
        update_product(pid, is_active=new_active)
        prod = get_product(pid)
        await callback.message.edit(
            f"{'✅ فعال' if new_active else '❌ غیرفعال'} شد: {prod['name']}",
            components=admin_product_detail_keyboard(pid, new_active)
        )
        return
    if data.startswith("admin_prod_"):
        pid = int(data.replace("admin_prod_", ""))
        prod = get_product(pid)
        if prod:
            txt = (
                f"📦 *{prod['name']}*\n"
                f"کد: {prod['catalog_code']} | دسته: {prod['category']}\n"
                f"Particle/ضخامت: {prod['particle_size']}\n"
                f"حجم/سایز: {prod['volume_size']}\n"
                f"قیمت: {prod['price']:,} تومان\n"
                f"موجودی: {prod['stock']} عدد\n"
                f"وضعیت: ✅ فعال"
            )
            await callback.message.edit(txt, components=admin_product_detail_keyboard(pid, prod["is_active"]))


async def _start_edit_setting(bot, callback, bale_id, data):
    key_map = {
        "admin_set_bank_card":  ("bank_card",     "شماره کارت جدید:"),
        "admin_set_bank_owner": ("bank_owner",    "نام صاحب حساب:"),
        "admin_set_channel":    ("channel_id",    "آیدی کانال:\n• متنی: @biox_official\n• عددی: -1001234567890"),
        "admin_set_welcome":    ("welcome_text",  "متن خوش‌آمدگویی:"),
        "admin_set_payment":    ("payment_text",  "متن راهنمای پرداخت:"),
        "admin_set_channel_url": ("channel_url",   "لینک کانال (مثال: https://ble.ir/biox_official):"),
        "admin_set_contact":    ("contact_text",  "متن تماس با ما:"),
        "admin_set_about":      ("about_text",    "متن درباره ما:"),
        "admin_set_commitment": ("commitment_text", "متن تعهدنامه:\n(این متن به مشتری نمایش داده می‌شود):"),
    }
    if data not in key_map:
        return
    key, prompt = key_map[data]
    cur = get_setting(key, "")
    set_state(bale_id, "A_EDIT_SETTING", {"setting_key": key})
    await callback.message.edit(f"{prompt}\n\nمقدار فعلی:\n{cur}")

# ── FAQ ──────────────────────────────────────────────────
async def _show_faq(bot, callback):
    faqs = get_faqs()
    await callback.message.edit("سوالات متداول:\nبرای حذف روی هر سوال کلیک کنید.", components=admin_faq_keyboard(faqs))

async def state_faq_question(bot, message):
    bale_id = int(message.author.user_id)
    if not is_super_admin(bale_id): return
    q = (message.content or "").strip()
    if len(q) < 3:
        await message.reply("سوال خیلی کوتاه است:"); return
    set_state(bale_id, "A_FAQ_A", {"faq_q": q})
    await message.reply(f"سوال: {q}\n\nحالا پاسخ را بنویسید:")

async def state_faq_answer(bot, message):
    bale_id = int(message.author.user_id)
    if not is_super_admin(bale_id): return
    _, d = get_state(bale_id)
    d = d or {}
    a = (message.content or "").strip()
    if len(a) < 3:
        await message.reply("پاسخ خیلی کوتاه است:"); return
    add_faq(d.get("faq_q",""), a)
    clear_state(bale_id)
    await message.reply("سوال و جواب اضافه شد.")

# ── روزنامه ──────────────────────────────────────────────
async def _show_newspaper(bot, callback):
    items = get_newspaper(20)
    await callback.message.edit("روزنامه:\nبرای حذف روی هر شماره کلیک کنید.", components=admin_newspaper_keyboard(items))

async def state_newspaper_title(bot, message):
    bale_id = int(message.author.user_id)
    if not is_super_admin(bale_id): return
    title = (message.content or "").strip()
    set_state(bale_id, "A_NP_URL", {"np_title": title})
    await message.reply(
        f"عنوان: {title}\n\n"
        "لینک PDF را وارد کنید\nیا فایل ارسال کنید\nیا «فایل» بنویسید تا فایل بفرستید:"
    )

async def state_newspaper_url(bot, message):
    bale_id = int(message.author.user_id)
    if not is_super_admin(bale_id): return
    _, d = get_state(bale_id)
    d = d or {}
    text = (message.content or "").strip()
    if text == "فایل":
        set_state(bale_id, "A_NP_FILE", d)
        await message.reply("فایل یا PDF روزنامه را ارسال کنید:"); return
    add_newspaper(d.get("np_title",""), url=text)
    clear_state(bale_id)
    await message.reply("روزنامه اضافه شد.")

async def state_newspaper_file(bot, message):
    bale_id = int(message.author.user_id)
    if not is_super_admin(bale_id): return
    _, d = get_state(bale_id)
    d = d or {}
    file_id = None
    if hasattr(message,"document") and message.document: file_id = message.document.file_id
    elif hasattr(message,"photo") and message.photo: file_id = message.photo.file_id
    if not file_id:
        await message.reply("فایل دریافت نشد."); return
    add_newspaper(d.get("np_title",""), file_id=file_id)
    clear_state(bale_id)
    await message.reply("روزنامه اضافه شد.")

# ── تیکت ─────────────────────────────────────────────────
async def _show_ticket_detail(bot, callback, bale_id, data):
    tid = int(data.replace("admin_ticket_",""))
    ticket = get_ticket_by_id(tid)
    if not ticket: return
    user = get_user(ticket["bale_id"])
    txt = (
        f"تیکت: {ticket['ticket_code']}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"کاربر: {user['full_name'] if user else '-'}\n"
        f"موضوع: {ticket['subject']}\n"
        f"تاریخ: {to_jalali(ticket['created_at'])}\n"
        f"وضعیت: {ticket['status']}\n\n"
        f"پیام: {ticket['message_text'] or '[فایل پیوست]'}\n\n"
        f"برای پاسخ، روی این پیام ریپلای کنید."
    )
    # ذخیره message_id برای ریپلای
    from bale import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("بازگشت به تیکت‌ها", callback_data="admin_tickets"), row=0)
    await callback.message.edit(txt, components=kb)

# ── افزودن محصول جدید با ساختار جدید ──────────────────────
async def state_add_product(bot, message):
    bale_id = int(message.author.user_id)
    if not is_super_admin(bale_id): return
    state, d = get_state(bale_id)
    d = d or {}
    text = (message.content or "").strip()

    steps = {
        "A_ADD_PROD_1": ("category",      "A_ADD_PROD_2", "زیردسته را وارد کنید:\n(xbone یا xpatch یا crosslinked)"),
        "A_ADD_PROD_2": ("sub_category",  "A_ADD_PROD_3", "PARTICLE SIZE یا ضخامت را وارد کنید:\nمثال: 150-1000 µM یا 0.3-0.5 mm"),
        "A_ADD_PROD_3": ("particle_size", "A_ADD_PROD_4", "حجم/سایز را وارد کنید:\nمثال: 0.5cc یا 10×10"),
        "A_ADD_PROD_4": ("volume_size",   "A_ADD_PROD_5", "کد کاتالوگ را وارد کنید:\nمثال: 4016"),
        "A_ADD_PROD_5": ("catalog_code",  "A_ADD_PROD_6", "نام محصول را وارد کنید:"),
        "A_ADD_PROD_6": ("name",          "A_ADD_PROD_7", "قیمت را به تومان وارد کنید:\n(اگر قیمت ندارد 0 بزنید)"),
    }

    if state in steps:
        field, next_state, prompt = steps[state]
        if state == "A_ADD_PROD_1":
            if text not in ["xbone", "xpatch", "crosslinked"]:
                await message.reply("مقادیر مجاز: xbone یا xpatch یا crosslinked"); return
        d[field] = text
        set_state(bale_id, next_state, d)
        await message.reply(f"ثبت شد.\n\n{prompt}")

    elif state == "A_ADD_PROD_7":
        price = text.replace(",","").replace("،","")
        if not price.isdigit():
            await message.reply("قیمت نامعتبر:"); return
        set_state(bale_id, "A_ADD_PROD_8", {**d, "price": int(price)})
        await message.reply("موجودی اولیه را وارد کنید:")

    elif state == "A_ADD_PROD_8":
        if not text.isdigit():
            await message.reply("عدد صحیح وارد کنید:"); return
        from database.db import add_product
        add_product(
            d.get("category","xbone"), d.get("sub_category","xbone"),
            d.get("particle_size",""), d.get("volume_size",""),
            d.get("catalog_code",""), d.get("name",""),
            d.get("price",0), int(text)
        )
        clear_state(bale_id)
        await message.reply(f"محصول {d.get('name','')} | {d.get('catalog_code','')} اضافه شد.")

# ── اقساط ────────────────────────────────────────────────
async def cb_installment_payment(bot, callback):
    bale_id = int(callback.from_user.user_id)
    if not is_super_admin(bale_id): return
    data = callback.data

    if data.startswith("inst_approve_"):
        parts = data.replace("inst_approve_","").split("_",1)
        payment_id = int(parts[0])
        order_num = parts[1] if len(parts)>1 else ""
        from database.db import approve_installment_payment, get_installment, get_user, has_pending_installment
        approve_installment_payment(payment_id)
        inst = get_installment(order_num)
        if inst:
            user_bale_id = inst["bale_id"]
            if inst["remaining_amount"] <= 0:
                # اقساط تموم شد
                from handlers.start import _make_main_kb
                await bot.send_message(user_bale_id,
                    f"اقساط سفارش {order_num} به پایان رسید!\n"
                    f"مبلغ کل پرداخت شده: {inst['total_amount']:,} تومان\n\nممنون از اعتماد شما.")
                await bot.send_message(user_bale_id, "منوی اصلی:", components=_make_main_kb(user_bale_id))
            else:
                await bot.send_message(user_bale_id,
                    f"قسط شما تایید شد!\nسفارش: {order_num}\n"
                    f"پرداخت شده تاکنون: {inst['paid_amount']:,} تومان\n"
                    f"مانده: {inst['remaining_amount']:,} تومان\n"
                    f"سررسید: {to_jalali(inst['due_date'])}")
        await callback.message.edit((callback.message.content or "") + "\n\n✅ قسط تایید شد")

    elif data.startswith("inst_reject_"):
        payment_id = int(data.replace("inst_reject_",""))
        await callback.message.edit((callback.message.content or "") + "\n\n❌ رد شد")

# ── گزارش دوره‌ای ─────────────────────────────────────────
async def cb_report_period(bot, callback):
    bale_id = int(callback.from_user.user_id)
    from database.db import has_staff_role
    if not is_super_admin(bale_id) and not has_staff_role(bale_id, "finance"): return
    days = int(callback.data.replace("rep_",""))
    from database.db import get_orders_by_period
    import json
    orders = get_orders_by_period(days)
    period_map = {30:"۱ ماه",90:"۳ ماه",180:"۶ ماه",365:"۱ سال"}
    period_fa = period_map.get(days,"")

    total_rev = sum(o["final_amount"] or 0 for o in orders)
    total_disc = sum(o["discount_amount"] or 0 for o in orders)

    # شمارش محصولات
    prod_count = {}
    for o in orders:
        try:
            items = json.loads(o["items"])
            for it in items:
                k = it["catalog_code"]
                prod_count[k] = prod_count.get(k,0) + it["qty"]
        except: pass

    txt = (
        f"گزارش {period_fa} گذشته\n━━━━━━━━━━━━━━━\n"
        f"تعداد سفارشات: {len(orders)}\n"
        f"درآمد کل: {total_rev:,} تومان\n"
        f"تخفیف داده شده: {total_disc:,} تومان\n"
        f"درآمد خالص: {total_rev-total_disc:,} تومان\n"
        f"━━━━━━━━━━━━━━━\n"
        f"محصولات فروخته شده:\n"
    )
    for k,v in sorted(prod_count.items(), key=lambda x: -x[1])[:10]:
        txt += f"• {k}: {v} عدد\n"

    from utils.keyboards import excel_period_keyboard
    from bale import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("دریافت اکسل این دوره", callback_data=f"excel_orders_{days}"), row=1)
    kb.add(InlineKeyboardButton("بازگشت", callback_data="admin_back_main"), row=2)
    await callback.message.edit(txt[:4000], components=kb)

async def cb_excel_orders(bot, callback):
    bale_id = int(callback.from_user.user_id)
    from database.db import has_staff_role
    if not is_super_admin(bale_id) and not has_staff_role(bale_id, "finance"): return
    days = int(callback.data.replace("excel_orders_",""))
    await callback.message.edit("در حال ساخت فایل اکسل...")
    from utils.excel_export import send_orders_excel
    await send_orders_excel(bot, bale_id, days)

# ── سفارشات تکمیل شده / در جریان ────────────────────────
async def _show_completed_orders(bot, callback, bale_id=None):
    if bale_id is None: bale_id = int(callback.from_user.user_id)
    from database.db import get_orders_completed
    orders = get_orders_completed()
    txt = f"سفارشات تکمیل شده ({len(orders)}):\n━━━━━━━━━━━━━━━\n"
    for o in orders[:15]:
        txt += f"✅ {o['order_number']} | {o['full_name']} | {o['final_amount']:,} ت\n"
        if o["tracking_code"]:
            txt += f"   رهگیری: {o['tracking_code']}\n"
    from bale import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("بازگشت", callback_data="admin_back_main"), row=1)
    await callback.message.edit(txt[:4000], components=kb)

async def _show_inprogress_orders(bot, callback, bale_id=None):
    if bale_id is None: bale_id = int(callback.from_user.user_id)
    from database.db import get_orders_in_progress
    orders = get_orders_in_progress()
    st = {"pending_payment":"💳","receipt_sent":"🔍","approved":"📦"}
    txt = f"سفارشات در جریان ({len(orders)}):\n━━━━━━━━━━━━━━━\n"
    for o in orders[:15]:
        txt += f"{st.get(o['status'],'•')} {o['order_number']} | {o['full_name']} | {o['final_amount']:,} ت\n"
    from bale import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("بازگشت", callback_data="admin_back_main"), row=1)
    await callback.message.edit(txt[:4000], components=kb)


async def cb_excel_customers(bot, callback):
    """ارسال اکسل مشتریان"""
    bale_id = int(callback.from_user.user_id)
    from database.db import has_staff_role
    if not is_super_admin(bale_id) and not has_staff_role(bale_id, "finance"):
        return
    await callback.message.edit("در حال ساخت فایل اکسل...")
    from utils.excel_export import send_customers_excel
    await send_customers_excel(bot, bale_id)

# ── اطلاعیه کارکنان ──────────────────────────────────────
async def _show_staff_news_mgmt(bot, callback, bale_id):
    from bale import InlineKeyboardMarkup, InlineKeyboardButton
    news = get_staff_news(20)
    kb = InlineKeyboardMarkup()
    for i, n in enumerate(news):
        kb.add(InlineKeyboardButton(f"حذف | {n['title'][:25]}", callback_data=f"admin_staff_news_del_{n['id']}"), row=i+1)
    kb.add(InlineKeyboardButton("افزودن اطلاعیه کارکنان", callback_data="admin_staff_news_add"), row=len(news)+1)
    kb.add(InlineKeyboardButton("بازگشت",                  callback_data="admin_back_main"),      row=len(news)+2)
    await callback.message.edit("اطلاعیه‌های کارکنان:", components=kb)


async def state_staff_news_title(bot, message):
    bale_id = int(message.author.user_id)
    if not is_super_admin(bale_id): return
    title = (message.content or "").strip()
    set_state(bale_id, "A_STAFF_NEWS_BODY", {"staff_news_title": title})
    await message.reply(f"عنوان: {title}\n\nمتن اطلاعیه را بنویسید:")


async def state_staff_news_body(bot, message):
    bale_id = int(message.author.user_id)
    if not is_super_admin(bale_id): return
    body = (message.content or "").strip()
    _, d = get_state(bale_id)
    d = d or {}
    title = d.get("staff_news_title", "")
    add_staff_news(title, body)
    clear_state(bale_id)

    # ارسال به همه کارکنان
    from database.db import get_all_staff
    all_staff = get_all_staff()
    staff_ids = list(set(s["bale_id"] for s in all_staff))
    sent = 0
    for sid in staff_ids:
        try:
            await bot.send_message(sid, f"اطلاعیه کارکنان\n\n{title}\n\n{body}")
            sent += 1
        except: pass
    await message.reply(f"اطلاعیه ثبت و برای {sent} نفر ارسال شد.")


# ── تسک کارکنان ──────────────────────────────────────────
async def state_task_title(bot, message):
    bale_id = int(message.author.user_id)
    if not is_super_admin(bale_id): return
    _, d = get_state(bale_id)
    d = d or {}
    title = (message.content or "").strip()
    if len(title) < 2:
        await message.reply("عنوان خیلی کوتاه است:")
        return
    d["task_title"] = title
    set_state(bale_id, "A_TASK_BODY", d)
    await message.reply(
        f"عنوان: {title}\n\n"
        "متن تسک را بنویسید یا فایل ارسال کنید:\n"
        "(یا «بدون متن» بنویسید)"
    )


async def state_task_body(bot, message):
    bale_id = int(message.author.user_id)
    if not is_super_admin(bale_id): return
    _, d = get_state(bale_id)
    d = d or {}

    title = d.get("task_title", "")
    target_id = d.get("task_target")
    body = None
    file_id = None
    ftype = None

    # فایل یا متن
    if hasattr(message, "photo") and message.photo:
        file_id = message.photo.file_id; ftype = "photo"
    elif hasattr(message, "photos") and message.photos:
        file_id = message.photos[-1].file_id; ftype = "photo"
    elif hasattr(message, "document") and message.document:
        file_id = message.document.file_id; ftype = "document"
    else:
        body = (message.content or "").strip()
        if body == "بدون متن":
            body = None

    add_task(target_id, title, body, file_id, ftype)
    clear_state(bale_id)

    # اطلاع‌رسانی به کارمند
    try:
        notif = f"📋 تسک جدید دریافت کردید:\n\n{title}"
        if body:
            notif += f"\n\n{body}"
        await bot.send_message(target_id, notif)
        if file_id:
            from bale import InputFile
            if ftype == "photo":
                await bot.send_photo(target_id, InputFile(file_id))
            else:
                await bot.send_document(target_id, InputFile(file_id))
    except Exception as e:
        pass

    await message.reply(f"✅ تسک «{title}» برای کارمند ارسال شد.")


async def state_fin_reject(bot, message):
    """دلیل رد چک/تعهدنامه"""
    bale_id = int(message.author.user_id)
    if not is_super_admin(bale_id):
        from database.db import has_staff_role
        if not has_staff_role(bale_id, "finance"):
            return
    _, d = get_state(bale_id)
    d = d or {}
    reason = (message.content or "").strip()
    order_num = d.get("order_num", "")
    doc = get_check_doc(order_num)
    if doc:
        update_check_doc(order_num, status="rejected", reject_reason=reason)
        update_order(order_num, status="rejected")
        await bot.send_message(doc["bale_id"],
            f"❌ درخواست سفارش {order_num} رد شد.\n\n"
            f"دلیل: {reason}\n\n"
            "برای اصلاح با پشتیبانی تماس بگیرید."
        )
    clear_state(bale_id)
    await message.reply(f"❌ رد شد. پیام به کاربر ارسال شد.")


# ── پنل مالی ─────────────────────────────────────────────
async def cmd_finance_panel(bot, message):
    bale_id = int(message.author.user_id)
    from database.db import has_staff_role
    if not is_super_admin(bale_id) and not has_staff_role(bale_id, "finance"):
        await message.reply("دسترسی ندارید.")
        return
    from utils.keyboards import finance_panel_keyboard
    await message.reply(
        "پنل مالی\n━━━━━━━━━━━━━━━\nاز منوی زیر انتخاب کنید:",
        components=finance_panel_keyboard()
    )
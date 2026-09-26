from utils.date_utils import to_jalali, now_jalali
from bale import InputFile
from database.db import (
    get_user, get_staff_roles, add_staff_report, STAFF_ROLES,
    get_state, set_state, clear_state,
    get_orders_by_status, update_order, get_order, get_all_products, get_product, update_product,
    clock_in, clock_out, get_today_attendance, get_staff_news,
    get_user_tasks, update_task_status
)
from bale import InlineKeyboardMarkup, InputFile, InlineKeyboardButton
from utils.keyboards import warehouse_main_keyboard


# ── منوی کارکنان ─────────────────────────────────────────
async def cmd_staff(bot, message):
    bale_id = int(message.author.user_id)
    user = get_user(bale_id)
    if not user or not user["full_name"]:
        await message.reply("❌ ابتدا /start را بزنید.")
        return

    roles = get_staff_roles(bale_id)
    if not roles:
        await message.reply("⛔ دسترسی پنل کارکنان برای شما فعال نشده.")
        return

    role_names = [STAFF_ROLES.get(r, r) for r in roles]
    role_text = " | ".join(role_names)

    # انباردار منوی مخصوص دارد
    if "warehouse" in roles:
        await message.reply(
            f"🏭 *پنل انباردار*\n"
            f"سلام {user['full_name']}\n"
            f"سمت: {role_text}\n\n"
            f"از منوی زیر انتخاب کنید:",
            components=warehouse_main_keyboard()
        )
        return

    # کارمند عادی
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("ثبت ورود / خروج",     callback_data="cb_attendance"),       row=1)
    kb.add(InlineKeyboardButton("ثبت گزارش روزانه",    callback_data="cb_staff_daily"),       row=2)
    kb.add(InlineKeyboardButton("گزارش‌های قبلی من",   callback_data="cb_staff_my_reports"),  row=3)
    kb.add(InlineKeyboardButton("اطلاعیه کارکنان",     callback_data="cb_staff_news"),        row=4)
    kb.add(InlineKeyboardButton("تسک‌های من",            callback_data="cb_staff_tasks"),       row=5)
    await message.reply(
        f"پنل کارکنان\n"
        f"سلام {user['full_name']}\n"
        f"سمت: {role_text}\n\n"
        f"از منوی زیر انتخاب کنید:",
        components=kb
    )


# ── گزارش کارمند ─────────────────────────────────────────
async def cb_staff_type(bot, callback):
    bale_id = int(callback.from_user.user_id)
    data = callback.data

    if data == "cb_attendance":
        att = get_today_attendance(bale_id)
        from bale import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup()
        if att is None or att["clock_out"] is not None:
            kb.add(InlineKeyboardButton("ثبت ورود", callback_data="cb_clock_in"), row=1)
            status = "امروز ورودی ثبت نشده." if att is None else                      f"آخرین شیفت:\nورود: {att['clock_in'][:5]} | خروج: {att['clock_out'][:5]}\nمدت: {att['total_minutes']} دقیقه"
        else:
            kb.add(InlineKeyboardButton("ثبت خروج", callback_data="cb_clock_out"), row=1)
            status = f"ورود ثبت شده: {att['clock_in'][:5]}\nمنتظر خروج..."
        await callback.message.edit(f"ورود و خروج\n\n{status}", components=kb)

    elif data == "cb_clock_in":
        result = clock_in(bale_id)
        if result is None:
            await callback.message.edit("قبلاً ورود ثبت کرده‌اید.")
            return
        await callback.message.edit(f"ورود ثبت شد\nساعت: {result}")

    elif data == "cb_clock_out":
        result = clock_out(bale_id)
        if result is None:
            await callback.message.edit("ابتدا باید ورود ثبت کنید.")
            return
        time_out, minutes = result
        hours = minutes // 60; mins = minutes % 60
        await callback.message.edit(
            f"خروج ثبت شد\nساعت: {time_out}\n"
            f"مدت کار: {hours} ساعت و {mins} دقیقه"
        )

    elif data == "cb_staff_news":
        news = get_staff_news(8)
        if not news:
            await callback.message.edit("اطلاعیه‌ای ثبت نشده.")
            return
        from bale import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup()
        for i, n in enumerate(news):
            kb.add(InlineKeyboardButton(n['title'], callback_data=f"cb_snews_{n['id']}"), row=i+1)
        await callback.message.edit("اطلاعیه‌های کارکنان:", components=kb)

    elif data.startswith("cb_snews_"):
        from database.db import get_conn
        nid = int(data.replace("cb_snews_",""))
        conn = get_conn()
        n = conn.execute("SELECT * FROM staff_news WHERE id=?", (nid,)).fetchone()
        conn.close()
        if n:
            await callback.message.edit(f"{n['title']}\n{to_jalali(n['created_at'])}\n\n{n['body']}")

    elif data == "cb_staff_tasks":
        tasks = get_user_tasks(bale_id)
        if not tasks:
            await callback.message.edit("تسکی برای شما ثبت نشده.")
            return
        from bale import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup()
        for i, t in enumerate(tasks[:10]):
            status_icon = "✅" if t["status"] == "done" else "📋"
            title = (t["title"] or "")[:25]
            kb.add(InlineKeyboardButton(f"{status_icon} {title}", callback_data=f"cb_task_{t['id']}"), row=i+1)
        await callback.message.edit("تسک‌های من:", components=kb)

    elif data.startswith("cb_task_done_"):
        task_id = int(data.replace("cb_task_done_",""))
        update_task_status(task_id, "done")
        await callback.message.edit("✅ تسک به عنوان انجام شده علامت‌گذاری شد.")

    elif data.startswith("cb_task_") and not data.startswith("cb_task_done_"):
        task_id = int(data.replace("cb_task_",""))
        from database.db import get_task
        t = get_task(task_id)
        if not t:
            return
        status = "انجام شده ✅" if t["status"] == "done" else "در انتظار 📋"
        txt = f"تسک: {t['title']}\nوضعیت: {status}\nتاریخ: {t['created_at'][:10]}"
        if t["body"]:
            txt += f"\n\n{t['body']}"
        from bale import InlineKeyboardMarkup, InlineKeyboardButton, InputFile
        kb = InlineKeyboardMarkup()
        if t["status"] != "done":
            kb.add(InlineKeyboardButton("✅ علامت‌گذاری به عنوان انجام شده", callback_data=f"cb_task_done_{task_id}"), row=1)
        kb.add(InlineKeyboardButton("بازگشت", callback_data="cb_staff_tasks"), row=2)
        if t["file_id"]:
            if t["file_type"] == "photo":
                await bot.send_photo(bale_id, InputFile(t["file_id"]), caption=txt)
            else:
                await bot.send_document(bale_id, InputFile(t["file_id"]), caption=txt)
            await callback.message.edit("جزئیات تسک:", components=kb)
        else:
            await callback.message.edit(txt, components=kb)

    elif data == "cb_staff_daily":
        set_state(bale_id, "W_STAFF_REPORT", {"report_type": "گزارش روزانه"})
        await callback.message.edit(
            "ثبت گزارش روزانه\n\n"
            "گزارش کار امروز خود را بنویسید:\n"
            "(می‌توانید متن، تصویر یا فایل ارسال کنید)"
        )
    elif data == "cb_staff_my_reports":
        from database.db import get_staff_reports_by_user
        reports = get_staff_reports_by_user(bale_id, 5)
        if not reports:
            await callback.message.edit("📋 هنوز گزارشی ثبت نکرده‌اید.")
            return
        txt = "📋 *گزارش‌های اخیر شما:*\n━━━━━━━━━━━━━━━\n"
        for r in reports:
            txt += (
                f"\n📅 {to_jalali(r['created_at'])}\n"
                f"نوع: {r['report_type']}\n"
                f"متن: {(r['report_text'] or '')[:100]}...\n"
            )
        await callback.message.edit(txt)


async def state_staff_report(bot, message):
    bale_id = int(message.author.user_id)
    text = (message.content or "").strip()
    _, d = get_state(bale_id)
    d = d or {}
    rtype = d.get("report_type", "گزارش")

    file_id = None
    file_type = None
    if hasattr(message, "photo") and message.photo:
        file_id = message.photo.file_id
        file_type = "photo"
    elif hasattr(message, "photos") and message.photos:
        file_id = message.photos[-1].file_id
        file_type = "photo"
    elif hasattr(message, "document") and message.document:
        file_id = message.document.file_id
        file_type = "document"

    if not text and not file_id:
        await message.reply("❌ گزارش خالی است:")
        return
    if text and len(text) < 5:
        await message.reply("❌ گزارش خیلی کوتاه است (حداقل ۵ کاراکتر):")
        return

    add_staff_report(bale_id, rtype, text or "-", file_id, file_type)
    clear_state(bale_id)
    user = get_user(bale_id)

    from bot import SUPER_ADMIN_IDS
    notif = (
        f"👔 *{rtype}*\n"
        f"از: {user['full_name']}\n"
        f"📅 {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        f"{text or '[فایل پیوست]'}"
    )
    for aid in SUPER_ADMIN_IDS:
        try:
            if file_id and file_type == "photo":
                await bot.send_photo(aid, InputFile(file_id), caption=notif)
            elif file_id and file_type == "document":
                await bot.send_document(aid, InputFile(file_id), caption=notif)
            else:
                await bot.send_message(aid, notif)
        except:
            pass

    await message.reply("✅ گزارش با موفقیت ثبت شد!")


# ── پنل انبار ────────────────────────────────────────────
async def cb_warehouse(bot, callback):
    bale_id = int(callback.from_user.user_id)
    roles = get_staff_roles(bale_id)
    if "warehouse" not in roles:
        await callback.message.edit("⛔ دسترسی ندارید.")
        return
    data = callback.data

    if data == "wh_back":
        await callback.message.edit(
            "🏭 *پنل انباردار*\nاز منوی زیر انتخاب کنید:",
            components=warehouse_main_keyboard()
        )

    elif data == "wh_ready_orders":
        await _show_ready_orders(bot, callback)

    elif data == "wh_stock":
        await _show_stock_manager(bot, callback)

    elif data.startswith("wh_order_"):
        order_num = data.replace("wh_order_", "")
        await _show_order_for_tracking(bot, callback, order_num)

    elif data.startswith("wh_track_"):
        order_num = data.replace("wh_track_", "")
        set_state(bale_id, "W_TRACKING_CODE", {"order_num": order_num})
        order = get_order(order_num)
        import json
        items = json.loads(order["items"])
        from database.db import get_user as gu
        customer = gu(order["bale_id"])
        txt = (
            f"📦 *سفارش {order_num}*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 {customer['full_name']}\n"
            f"📱 {customer['phone']}\n"
            f"🏠 آدرس: {customer['address'] or '-'}\n"
            f"━━━━━━━━━━━━━━━\n"
        )
        for i in items:
            txt += f"• {i['catalog_code']} | {i['size']} × {i['qty']}\n"
        txt += "\n📮 کد رهگیری پستی را وارد کنید:"
        await callback.message.edit(txt)

    elif data.startswith("wh_stock_edit_"):
        pid = int(data.replace("wh_stock_edit_", ""))
        prod = get_product(pid)
        set_state(bale_id, "W_WH_STOCK", {"pid": pid})
        await callback.message.edit(
            f"📦 *{prod['name']}*\n"
            f"موجودی فعلی: {prod['stock']} عدد\n\n"
            f"موجودی جدید را وارد کنید:"
        )


async def _show_ready_orders(bot, callback):
    orders = get_orders_by_status("approved")
    if not orders:
        await callback.message.edit(
            "📦 سفارش آماده ارسالی وجود ندارد.",
            components=warehouse_main_keyboard()
        )
        return
    kb = InlineKeyboardMarkup()
    for i, o in enumerate(orders[:10]):
        import json
        items = json.loads(o["items"])
        items_summary = ", ".join(f"{it['catalog_code']}×{it['qty']}" for it in items)
        kb.add(InlineKeyboardButton(
            f"📦 {o['order_number']} | {o['full_name'][:10]} | {items_summary[:20]}",
            callback_data=f"wh_order_{o['order_number']}"
        ), row=i)
    kb.add(InlineKeyboardButton("🔙 بازگشت", callback_data="wh_back"), row=len(orders[:10]))
    await callback.message.edit(
        f"📦 *سفارش‌های آماده ارسال ({len(orders)}):*",
        components=kb
    )


async def _show_order_for_tracking(bot, callback, order_num):
    order = get_order(order_num)
    if not order:
        return
    import json
    items = json.loads(order["items"])
    from database.db import get_user as gu
    customer = gu(order["bale_id"])

    txt = (
        f"📦 *سفارش {order_num}*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 {customer['full_name']}\n"
        f"📱 {customer['phone'] or '-'}\n"
        f"🏠 {customer['address'] or '-'}\n"
        f"━━━━━━━━━━━━━━━\n"
    )
    for i in items:
        txt += f"• {i['catalog_code']} | {i['size']} × {i['qty']}\n"

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("📮 ثبت کد رهگیری", callback_data=f"wh_track_{order_num}"), row=0)
    kb.add(InlineKeyboardButton("🔙 بازگشت",        callback_data="wh_ready_orders"),        row=1)
    await callback.message.edit(txt, components=kb)


async def _show_stock_manager(bot, callback):
    prods = get_all_products()
    kb = InlineKeyboardMarkup()
    for i, p in enumerate(prods):
        icon = "✅" if p["stock"] > 10 else ("⚠️" if p["stock"] > 0 else "❌")
        kb.add(InlineKeyboardButton(
            f"{icon} {p['catalog_code']} | {p['name'][:15]}: {p['stock']} عدد",
            callback_data=f"wh_stock_edit_{p['id']}"
        ), row=i)
    kb.add(InlineKeyboardButton("🔙 بازگشت", callback_data="wh_back"), row=len(prods))
    await callback.message.edit("🏭 *مدیریت موجودی انبار:*", components=kb)


async def state_tracking_code(bot, message):
    bale_id = int(message.author.user_id)
    code = (message.content or "").strip()
    if len(code) < 5:
        await message.reply("❌ کد رهگیری نامعتبر است:")
        return
    _, d = get_state(bale_id)
    d = d or {}
    order_num = d.get("order_num")
    if not order_num:
        await message.reply("❌ خطا. دوباره از منو انتخاب کنید.")
        return

    update_order(order_num, status="shipped", tracking_code=code)
    clear_state(bale_id)

    order = get_order(order_num)
    await message.reply(f"✅ کد رهگیری *{code}* برای سفارش {order_num} ثبت شد.")

    # پیام به مشتری
    try:
        await bot.send_message(
            order["bale_id"],
            f"📦 *سفارش شما ارسال شد!*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📋 سفارش: {order_num}\n"
            f"📮 کد رهگیری پستی: *{code}*\n\n"
            f"می‌توانید از طریق سایت اداره پست وضعیت مرسوله را پیگیری کنید."
        )
    except:
        pass


async def state_wh_stock(bot, message):
    bale_id = int(message.author.user_id)
    text = (message.content or "").strip()
    if not text.isdigit():
        await message.reply("❌ عدد صحیح وارد کنید:")
        return
    _, d = get_state(bale_id)
    pid = (d or {}).get("pid")
    update_product(pid, stock=int(text))
    clear_state(bale_id)
    await message.reply(f"✅ موجودی به {text} عدد تغییر کرد.")


# ── ورود و خروج ──────────────────────────────────────────
async def cmd_attendance(bot, message):
    bale_id = int(message.author.user_id)
    att = get_today_attendance(bale_id)

    from bale import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup()

    if att is None or att["clock_out"] is not None:
        # هنوز ورود نزده یا قبلاً خروج زده
        kb.add(InlineKeyboardButton("ثبت ورود", callback_data="cb_clock_in"),  row=1)
        status = "امروز ورودی ثبت نشده." if att is None else \
                 f"آخرین شیفت:\nورود: {att['clock_in'][:5]} | خروج: {att['clock_out'][:5]}\nمدت: {att['total_minutes']} دقیقه"
    else:
        # ورود زده ولی خروج نزده
        kb.add(InlineKeyboardButton("ثبت خروج", callback_data="cb_clock_out"), row=1)
        status = f"ورود ثبت شده: {att['clock_in'][:5]}\nمنتظر خروج..."

    await message.reply(f"ورود و خروج\n\n{status}", components=kb)


async def cb_clock_in(bot, callback):
    bale_id = int(callback.from_user.user_id)
    result = clock_in(bale_id)
    if result is None:
        await callback.message.edit("قبلاً ورود ثبت کرده‌اید. ابتدا خروج بزنید.")
        return
    await callback.message.edit(
        f"ورود ثبت شد\nساعت: {result}\n\nبرای ثبت خروج دوباره از منوی ورود/خروج اقدام کنید."
    )


async def cb_clock_out(bot, callback):
    bale_id = int(callback.from_user.user_id)
    result = clock_out(bale_id)
    if result is None:
        await callback.message.edit("ابتدا باید ورود ثبت کنید.")
        return
    time_out, minutes = result
    hours = minutes // 60
    mins  = minutes % 60
    await callback.message.edit(
        f"خروج ثبت شد\nساعت: {time_out}\n"
        f"مدت کار: {hours} ساعت و {mins} دقیقه\n\n"
        f"حالا می‌توانید گزارش کار خود را ثبت کنید."
    )


# ── اطلاعیه کارکنان ──────────────────────────────────────
async def cmd_staff_news(bot, message):
    news = get_staff_news(8)
    if not news:
        await message.reply("اطلاعیه‌ای برای کارکنان ثبت نشده.")
        return
    from bale import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup()
    for i, n in enumerate(news):
        kb.add(InlineKeyboardButton(n['title'], callback_data=f"cb_snews_{n['id']}"), row=i+1)
    await message.reply("اطلاعیه‌های کارکنان:", components=kb)


async def cb_staff_news_item(bot, callback):
    from database.db import get_conn
    nid = int(callback.data.replace("cb_snews_", ""))
    conn = get_conn()
    n = conn.execute("SELECT * FROM staff_news WHERE id=?", (nid,)).fetchone()
    conn.close()
    if n:
        await callback.message.edit(f"{n['title']}\n{to_jalali(n['created_at'])}\n\n{n['body']}")


# ── تسک‌های کارمند ───────────────────────────────────────
async def cmd_my_tasks(bot, message):
    bale_id = int(message.author.user_id)
    tasks = get_user_tasks(bale_id)
    if not tasks:
        await message.reply("تسکی برای شما ثبت نشده.")
        return
    from bale import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup()
    for i, t in enumerate(tasks[:10]):
        status_icon = "✅" if t["status"] == "done" else "📋"
        title = (t["title"] or "")[:25]
        kb.add(InlineKeyboardButton(f"{status_icon} {title}", callback_data=f"cb_task_{t['id']}"), row=i+1)
    await message.reply("تسک‌های من:", components=kb)

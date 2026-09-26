from utils.date_utils import to_jalali
from bale import InputFile
from database.db import (
    get_setting, get_news, get_news_item, get_catalog_items,
    get_faqs, get_faq, get_newspaper,
    create_ticket, get_ticket_by_code, update_ticket,
    set_state, clear_state, get_state, get_user
)
from bale import InlineKeyboardMarkup, InputFile, InlineKeyboardButton
from utils.keyboards import support_subject_keyboard, faq_keyboard

async def cmd_news(bot, message):
    news_list = get_news(8)
    if not news_list:
        await message.reply("در حال حاضر اطلاعیه‌ای موجود نیست.")
        return
    kb = InlineKeyboardMarkup()
    for i, n in enumerate(news_list):
        kb.add(InlineKeyboardButton(n['title'], callback_data=f"cb_news_{n['id']}"), row=i)
    await message.reply("اطلاعیه‌ها:", components=kb)

async def cb_news_item(bot, callback):
    nid = int(callback.data.replace("cb_news_",""))
    n = get_news_item(nid)
    if n:
        await callback.message.edit(f"{n['title']}\n{to_jalali(n['created_at'])}\n\n{n['body']}")

async def cmd_newspaper(bot, message):
    items = get_newspaper(10)
    if not items:
        await message.reply("شماره‌ای از روزنامه موجود نیست.")
        return
    kb = InlineKeyboardMarkup()
    for i, n in enumerate(items):
        kb.add(InlineKeyboardButton(n['title'], callback_data=f"cb_np_{n['id']}"), row=i)
    await message.reply("روزنامه:", components=kb)

async def cb_newspaper_item(bot, callback):
    from database.db import get_conn
    nid = int(callback.data.replace("cb_np_",""))
    conn = get_conn()
    item = conn.execute("SELECT * FROM newspaper WHERE id=?", (nid,)).fetchone()
    conn.close()
    if not item: return
    bale_id = int(callback.from_user.user_id)
    if item["url"]:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("مشاهده", url=item["url"]), row=0)
        await callback.message.edit(item["title"], components=kb)
    elif item["file_id"]:
        await bot.send_document(bale_id, InputFile(item["file_id"]), caption=item["title"])

async def cmd_catalog(bot, message):
    items = get_catalog_items(20)
    if not items:
        await message.reply("کاتالوگ در دسترس نیست.")
        return
    kb = InlineKeyboardMarkup()
    for i, item in enumerate(items):
        kb.add(InlineKeyboardButton(item['title'], callback_data=f"cb_catalog_{item['id']}"), row=i)
    await message.reply("کاتالوگ و اطلاعات:", components=kb)

async def cb_catalog_item(bot, callback):
    from database.db import get_conn
    cid = int(callback.data.replace("cb_catalog_",""))
    conn = get_conn()
    item = conn.execute("SELECT * FROM catalog_items WHERE id=?", (cid,)).fetchone()
    conn.close()
    if not item: return
    bale_id = int(callback.from_user.user_id)
    if item["url"]:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("مشاهده", url=item["url"]), row=0)
        await callback.message.edit(f"{item['title']}\n\n{item['description'] or ''}", components=kb)
    elif item["file_id"]:
        try:
            if item["item_type"] == "video": await bot.send_video(bale_id, InputFile(item["file_id"]), caption=item["title"])
            else: await bot.send_document(bale_id, InputFile(item["file_id"]), caption=item["title"])
        except: await callback.message.edit(f"خطا در ارسال: {item['title']}")

async def cmd_contact(bot, message):
    text = get_setting("contact_text","اطلاعات تماس")
    await message.reply(f"ارتباط با ما\n\n{text}")

async def cmd_faq(bot, message):
    faqs = get_faqs()
    if not faqs:
        await message.reply("سوالی ثبت نشده.")
        return
    await message.reply("سوالات متداول\n\nروی هر سوال بزنید:", components=faq_keyboard(faqs))

async def cb_faq_item(bot, callback):
    fid = int(callback.data.replace("cb_faq_",""))
    f = get_faq(fid)
    if f:
        faqs = get_faqs()
        kb = faq_keyboard(faqs)
        await callback.message.edit(f"سوال: {f['question']}\n\nپاسخ:\n{f['answer']}", components=kb)

# ── پشتیبانی (تیکت) ──
async def cmd_support(bot, message):
    bale_id = int(message.author.user_id)
    clear_state(bale_id)
    await message.reply("پشتیبانی\n\nموضوع مشکل خود را انتخاب کنید:", components=support_subject_keyboard())

async def cb_support_subject(bot, callback):
    bale_id = int(callback.from_user.user_id)
    subject_map = {
        "cb_sup_financial": "مالی",
        "cb_sup_quality":   "کیفیت",
        "cb_sup_shipping":  "ارسال",
        "cb_sup_other":     "سایر",
    }
    subject = subject_map.get(callback.data)
    if not subject: return
    set_state(bale_id, "W_TICKET_MSG", {"subject": subject})
    await callback.message.edit(
        f"موضوع: {subject}\n\n"
        "پیام خود را ارسال کنید:\n(می‌توانید متن، تصویر یا فایل ارسال کنید)"
    )

async def state_ticket_message(bot, message):
    bale_id = int(message.author.user_id)
    _, d = get_state(bale_id)
    d = d or {}
    subject = d.get("subject", "سایر")

    text = (message.content or "").strip()
    file_id = None; file_type = None

    if hasattr(message,"photo") and message.photo:
        file_id = message.photo.file_id; file_type = "photo"
    elif hasattr(message,"photos") and message.photos:
        file_id = message.photos[-1].file_id; file_type = "photo"
    elif hasattr(message,"document") and message.document:
        file_id = message.document.file_id; file_type = "document"
    elif hasattr(message,"voice") and message.voice:
        file_id = message.voice.file_id; file_type = "voice"

    if not text and not file_id:
        await message.reply("پیام خالی است. متن، تصویر یا فایل ارسال کنید:"); return

    code = create_ticket(bale_id, subject, text or None, file_id, file_type)
    clear_state(bale_id)
    await message.reply(f"پیام شما دریافت شد.\nموضوع: {subject}\nکد رهگیری: {code}\n\nپس از بررسی پاسخ برایتان ارسال می‌شود.")

    # ارسال به ادمین پشتیبانی
    from bot import SUPER_ADMIN_IDS
    user = get_user(bale_id)
    notif = (
        f"تیکت جدید\n━━━━━━━━━━━━━━━\n"
        f"{user['full_name']} | {user['phone']}\n"
        f"موضوع: {subject}\nکد: {code}\n"
    )
    if text: notif += f"پیام: {text[:300]}"

    # ارسال به ادمین با reply_to برای قابلیت ریپلای
    support_id = get_setting("support_admin_id", "")
    admin_ids = SUPER_ADMIN_IDS.copy()
    if support_id and support_id.isdigit():
        sid = int(support_id)
        if sid not in admin_ids:
            admin_ids.append(sid)

    for aid in admin_ids:
        try:
            sent = None
            if file_id and file_type == "photo":
                sent = await bot.send_photo(aid, InputFile(file_id), caption=notif)
            elif file_id and file_type == "document":
                sent = await bot.send_document(aid, InputFile(file_id), caption=notif)
            elif file_id and file_type == "voice":
                sent = await bot.send_voice(aid, InputFile(file_id), caption=notif)
            else:
                sent = await bot.send_message(aid, notif)
            # ذخیره message_id برای reply
            if sent and aid == admin_ids[0]:
                update_ticket(code, admin_message_id=getattr(sent, 'message_id', 0) or getattr(sent, 'id', 0))
        except: pass

async def handle_admin_ticket_reply(bot, message):
    """
    وقتی ادمین روی پیام تیکت ریپلای می‌کنه پاسخ به کاربر ارسال می‌شه
    """
    from bot import SUPER_ADMIN_IDS
    bale_id = int(message.author.user_id)
    if bale_id not in SUPER_ADMIN_IDS:
        return False

    # بررسی اینکه این ریپلای هست
    reply_to = getattr(message, "reply_to_message", None) or getattr(message, "reply_to", None)
    if not reply_to:
        return False

    reply_msg_id = getattr(reply_to, "message_id", None) or getattr(reply_to, "id", None)
    if not reply_msg_id:
        return False

    # پیدا کردن تیکت بر اساس admin_message_id
    from database.db import get_conn
    conn = get_conn()
    ticket = conn.execute("SELECT * FROM tickets WHERE admin_message_id=?", (reply_msg_id,)).fetchone()
    conn.close()
    if not ticket:
        return False

    reply_text = (message.content or "").strip()
    if not reply_text:
        return False

    # ارسال پاسخ به کاربر
    try:
        await bot.send_message(
            ticket["bale_id"],
            f"پاسخ پشتیبانی\n━━━━━━━━━━━━━━━\nکد تیکت: {ticket['ticket_code']}\nموضوع: {ticket['subject']}\n\n{reply_text}"
        )
        update_ticket(ticket["ticket_code"], status="answered")
        await message.reply(f"پاسخ به کاربر ارسال شد. (تیکت: {ticket['ticket_code']})")
    except Exception as e:
        await message.reply(f"خطا در ارسال پاسخ: {e}")
    return True

async def cmd_about(bot, message):
    from database.db import get_setting
    text = get_setting("about_text", "شرکت BioX")
    await message.reply(f"درباره ما\n\n{text}")

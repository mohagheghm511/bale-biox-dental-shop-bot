from database.db import get_user, upsert_user, update_user, get_state, set_state, clear_state, get_setting, get_staff_roles
from utils.keyboards import join_channel_keyboard, role_keyboard, role_confirm_keyboard, main_kb, phone_request_keyboard
from handlers.membership import handle_check_membership_callback

ROLES = {
    "cb_role_surgeon":   "🔬 جراح دندانپزشک",
    "cb_role_assistant": "🩺 دستیار دندانپزشک",
    "cb_role_secretary": "📋 منشی",
    "cb_role_sales":     "🤝 نماینده",
}

def _is_admin(bale_id):
    from bot import SUPER_ADMIN_IDS
    return bale_id in SUPER_ADMIN_IDS

def _make_main_kb(bale_id):
    roles = get_staff_roles(bale_id)
    from database.db import has_pending_installment
    return main_kb(
        is_admin=_is_admin(bale_id),
        is_staff="employee" in roles,
        is_warehouse="warehouse" in roles,
        has_installment=has_pending_installment(bale_id),
        is_finance="finance" in roles
    )

async def cmd_start(bot, message):
    bale_id = int(message.author.user_id)
    upsert_user(bale_id)
    user = get_user(bale_id)
    # اگه قبلاً ثبت‌نام کرده مستقیم منو
    if user and user["full_name"] and user["role"]:
        await cmd_main_menu(bot, message)
        return
    # شروع ثبت‌نام (عضویت قبلاً در bot.py چک شده)
    set_state(bale_id, "W_NAME")
    welcome = get_setting("welcome_text", "به پلتفرم اطلاع‌رسانی شرکت دانش بنیان ایده زیست فارمد (BioX) خوش آمدید.")
    await message.reply(f"{welcome}\n\nلطفاً نام و نام خانوادگی خود را وارد کنید:")

async def cb_joined(bot, callback):
    bale_id = int(callback.from_user.user_id)
    upsert_user(bale_id)
    is_ok = await handle_check_membership_callback(callback, bot)
    if not is_ok:
        return
    user = get_user(bale_id)
    if user and user["full_name"] and user["role"]:
        await callback.message.edit("عضویت تایید شد!")
        await bot.send_message(bale_id, f"سلام {user['full_name']}\n\nمنوی اصلی:", components=_make_main_kb(bale_id))
        return
    set_state(bale_id, "W_NAME")
    await callback.message.edit("لطفاً نام و نام خانوادگی خود را وارد کنید:")

async def state_name(bot, message):
    bale_id = int(message.author.user_id)
    name = (message.content or "").strip()
    if len(name) < 3:
        await message.reply("نام باید حداقل ۳ حرف باشد:")
        return
    update_user(bale_id, full_name=name)
    set_state(bale_id, "W_PHONE")
    # بدون تشکر — مستقیم درخواست شماره
    await message.reply(
        "لطفا برای تایید هویت، روی دکمه اشتراک‌گذاری شماره تماس کلیک کنید.",
        components=phone_request_keyboard()
    )

async def state_phone(bot, message):
    bale_id = int(message.author.user_id)
    phone = ""
    if hasattr(message, "contact") and message.contact:
        phone = str(message.contact.phone_number or "").strip().replace("+", "").replace(" ", "")
        if phone.startswith("98"):
            phone = "0" + phone[2:]
        elif not phone.startswith("0"):
            phone = "0" + phone
    else:
        phone = (message.content or "").strip().replace(" ", "").replace("-", "").replace("+", "")
        if phone.startswith("0098"):
            phone = "0" + phone[4:]
        elif phone.startswith("98"):
            phone = "0" + phone[2:]

    if not (phone.startswith("09") and len(phone) == 11 and phone.isdigit()):
        await message.reply("شماره نامعتبر است.\nمثال: 09121234567\nیا از دکمه ارسال خودکار استفاده کنید.")
        return
    update_user(bale_id, phone=phone)
    set_state(bale_id, "W_ROLE")
    await message.reply(
        "تخصص خود را انتخاب کنید:\n\n"
        "⚠️ توجه: سمت/تخصص پس از ثبت قابل ویرایش نیست.\n"
        "لطفاً با دقت انتخاب کنید.",
        components=role_keyboard()
    )

async def cb_role(bot, callback):
    bale_id = int(callback.from_user.user_id)
    data = callback.data

    # سایر — درخواست تایپ سمت
    if data == "cb_role_other":
        set_state(bale_id, "W_ROLE_OTHER")
        await callback.message.edit(
            "سمت/نقش کاری خود را بنویسید:\n"
            "(مثال: مدیر فروش، بازاریاب، مسئول انبار...)"
        )
        return

    # تغییر — برگشت به انتخاب تخصص
    if data == "cb_role_change":
        set_state(bale_id, "W_ROLE")
        await callback.message.edit(
            "تخصص خود را انتخاب کنید:\n\n"
            "⚠️ توجه: سمت/تخصص پس از ثبت قابل ویرایش نیست.\n"
            "لطفاً با دقت انتخاب کنید.",
            components=role_keyboard()
        )
        return

    # تأیید نهایی
    if data == "cb_role_confirm":
        _, d = get_state(bale_id)
        d = d or {}
        role = d.get("pending_role", "")
        if not role:
            return
        update_user(bale_id, role=role)
        clear_state(bale_id)
        user = get_user(bale_id)
        await callback.message.edit(f"پروفایل شما با موفقیت ایجاد شد.\nسمت: {role}")
        await bot.send_message(bale_id, f"{user['full_name']} خوش آمدید\n\nمنوی اصلی:", components=_make_main_kb(bale_id))
        return

    # انتخاب تخصص از لیست
    role = ROLES.get(data)
    if not role:
        return
    # ذخیره موقت و نمایش تأییدیه
    _, d = get_state(bale_id)
    d = d or {}
    d["pending_role"] = role
    set_state(bale_id, "W_ROLE_CONFIRM", d)
    await callback.message.edit(
        f"سمت انتخابی: {role}\n\n"
        "آیا از انتخاب سمت خود اطمینان دارید؟\n"
        "⚠️ پس از تأیید قابل تغییر نیست.",
        components=role_confirm_keyboard(role)
    )

async def cmd_main_menu(bot, message):
    bale_id = int(message.author.user_id)
    clear_state(bale_id)
    user = get_user(bale_id)
    name = user["full_name"] if user and user["full_name"] else "کاربر"
    await message.reply(f"سلام {name}\n\nمنوی اصلی BioX:", components=_make_main_kb(bale_id))

async def _send_main_menu(bot, bale_id, message):
    clear_state(bale_id)
    user = get_user(bale_id)
    name = user["full_name"] if user and user["full_name"] else "کاربر"
    await bot.send_message(bale_id, f"سلام {name}\n\nمنوی اصلی BioX:", components=_make_main_kb(bale_id))


async def state_role_other(bot, message):
    """کاربر سمت سایر را تایپ کرد"""
    bale_id = int(message.author.user_id)
    state, d = get_state(bale_id)
    if state != "W_ROLE_OTHER":
        return
    d = d or {}
    role_text = (message.content or "").strip()
    if len(role_text) < 2:
        await message.reply("سمت وارد شده خیلی کوتاه است. دوباره بنویسید:")
        return
    # ذخیره موقت و نمایش تأییدیه
    d["pending_role"] = role_text
    set_state(bale_id, "W_ROLE_CONFIRM", d)
    await message.reply(
        f"سمت وارد شده: {role_text}\n\n"
        "آیا از سمت وارد شده اطمینان دارید؟\n"
        "⚠️ پس از تأیید قابل تغییر نیست.",
        components=role_confirm_keyboard(role_text)
    )

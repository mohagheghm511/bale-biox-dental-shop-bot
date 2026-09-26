from database.db import get_setting
from utils.keyboards import join_channel_keyboard

# ── آیدی پیش‌فرض کانال — اینجا وارد کنید ──────────────────
DEFAULT_CHANNEL_ID  = "-1001234567890"   # ← آیدی عددی کانال خود را اینجا بگذارید
DEFAULT_CHANNEL_URL = "https://ble.ir/biox_official"  # ← لینک کانال
# ────────────────────────────────────────────────────────────

def _get_channel_id():
    """
    اول از دیتابیس می‌خونه، اگه تنظیم نشده از DEFAULT استفاده می‌کنه
    """
    val = get_setting("channel_id", "").strip()
    if not val:
        val = DEFAULT_CHANNEL_ID
    clean = val.lstrip('@')
    if clean.lstrip('-').isdigit():
        return int(clean)
    return val if val.startswith('@') else f"@{val}"

def get_channel_url():
    val = get_setting("channel_id", "").strip().lstrip('@')
    if not val:
        return get_setting("channel_url", DEFAULT_CHANNEL_URL) or DEFAULT_CHANNEL_URL
    if val.lstrip('-').isdigit():
        return get_setting("channel_url", DEFAULT_CHANNEL_URL) or DEFAULT_CHANNEL_URL
    return f"https://ble.ir/{val}"

async def check_membership(user_id: int, bot) -> bool:
    """True = اجازه ورود | False = باید عضو بشه"""
    if get_setting("channel_required", "1") != "1":
        return True

    channel_id = _get_channel_id()
    if not channel_id:
        return True

    try:
        member = await bot.get_chat_member(channel_id, user_id)
        if member is None:
            print(f"[Membership] user {user_id}: None → not member")
            return False
        status = str(member.status).lower().strip()
        is_member_flag = getattr(member, 'is_member', None)
        print(f"[Membership] user {user_id}: status='{status}', is_member={is_member_flag}")
        if status in ["creator", "administrator", "member"]:
            return True
        if is_member_flag is True:
            return True
        return False
    except Exception as e:
        print(f"[Membership] Error checking user {user_id}: {e}")
        return False

async def send_join_prompt(message, bot):
    channel_url = get_channel_url()
    welcome = get_setting("welcome_text", "به پلتفرم اطلاع‌رسانی شرکت دانش بنیان ایده زیست فارمد (BioX) خوش آمدید.")
    # گرفتن اسم کاربر از حساب بله
    author = getattr(message, "author", None)
    first = getattr(author, "first_name", "") or ""
    last  = getattr(author, "last_name", "")  or ""
    name  = (first + " " + last).strip() or ""
    greeting = f"سلام {name}\n\n" if name else ""
    await message.reply(
        f"سلام {name} عزیز\n\n{welcome}\n\nبرای استفاده از خدمات لطفاً ابتدا وارد کانال شوید:",
        components=join_channel_keyboard(channel_url)
    )

async def handle_check_membership_callback(cb, bot) -> bool:
    user_id = int(cb.from_user.user_id)
    is_ok = await check_membership(user_id, bot)
    if not is_ok:
        channel_url = get_channel_url()
        await cb.message.edit(
            "هنوز عضو کانال نشده‌اید!\n\nلطفاً ابتدا عضو شوید، سپس دوباره «عضو شدم» را بزنید.",
            components=join_channel_keyboard(channel_url)
        )
        return False
    return True

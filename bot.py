import logging
import os
from pathlib import Path

# load .env (optional, no dependency)
_env = Path(__file__).parent / ".env"
if _env.exists():
    for _l in _env.read_text(encoding="utf-8").splitlines():
        _l = _l.strip()
        if _l and not _l.startswith("#") and "=" in _l:
            _k, _v = _l.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())
import traceback
from bale import Bot, Message, CallbackQuery
from database.db import init_db

# ══════════════════════════════════════════════════════════
SUPER_ADMIN_IDS = [int(x) for x in os.getenv("SUPER_ADMIN_IDS", "").split(",") if x.strip().isdigit()]   # ← در فایل .env تنظیم کنید
BOT_TOKEN = os.getenv("BOT_TOKEN", "")   # ← در فایل .env تنظیم کنید
# ══════════════════════════════════════════════════════════

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler("biox.log", encoding="utf-8"), logging.StreamHandler()],
)
log = logging.getLogger(__name__)
bot = Bot(token=BOT_TOKEN)


async def _is_member(bale_id: int) -> bool:
    """چک عضویت — ادمین و مالی همیشه True"""
    if bale_id in SUPER_ADMIN_IDS:
        return True
    from handlers.membership import check_membership
    return await check_membership(bale_id, bot)


async def _ask_join(message_or_callback, is_callback=False):
    """ارسال پیام عضویت"""
    from handlers.membership import send_join_prompt
    if is_callback:
        from handlers.membership import get_channel_url
        from utils.keyboards import join_channel_keyboard
        await message_or_callback.message.edit(
            "برای استفاده از ربات باید در کانال ما عضو باشید.\n\n"
            "۱. روی دکمه «عضویت در کانال» کلیک کنید\n"
            "۲. عضو کانال شوید\n"
            "۳. برگردید و «عضو شدم» را بزنید",
            components=join_channel_keyboard(get_channel_url())
        )
    else:
        await send_join_prompt(message_or_callback, bot)


@bot.event
async def on_ready():
    init_db()
    log.info("✅ ربات BioX آماده است")
    # یادآور اقساط هر روز ساعت ۱۰
    import asyncio
    asyncio.get_event_loop().create_task(_installment_reminder_loop())

async def _installment_reminder_loop():
    import asyncio
    from datetime import datetime, timedelta
    while True:
        now = datetime.now()
        # هر ۲۴ ساعت یکبار
        await asyncio.sleep(86400)
        try:
            await _check_installment_reminders()
        except Exception as e:
            log.error(f"خطا در یادآور اقساط: {e}")

async def _check_installment_reminders():
    from database.db import get_all_pending_installments
    from datetime import datetime, timedelta
    installments = get_all_pending_installments()
    today = datetime.now().date()
    for inst in installments:
        try:
            due = datetime.strptime(inst["due_date"], "%Y/%m/%d").date()
            days_left = (due - today).days
            if days_left in [7, 3]:
                await bot.send_message(
                    inst["bale_id"],
                    f"یادآور پرداخت اقساط\n━━━━━━━━━━━━━━━\n"
                    f"سفارش: {inst['order_number']}\n"
                    f"مانده: {inst['remaining_amount']:,} تومان\n"
                    f"سررسید: {inst['due_date']}\n"
                    f"⏰ {days_left} روز تا سررسید مانده"
                )
        except Exception as e:
            log.error(f"خطا یادآور قسط {inst['order_number']}: {e}")


@bot.event
async def on_message(message: Message):
    try:
        if not message.author: return
        bale_id = int(message.author.user_id)
        text = (message.content or "").strip()

        from database.db import get_user
        from handlers.info import handle_admin_ticket_reply

        user = get_user(bale_id)
        if user and user["is_banned"]:
            await message.reply("دسترسی شما مسدود شده است.")
            return

        # ریپلای ادمین برای تیکت
        if bale_id in SUPER_ADMIN_IDS:
            if await handle_admin_ticket_reply(bot, message):
                return

        # ── چک عضویت — برای همه پیام‌ها حتی /start ──
        if not await _is_member(bale_id):
            await _ask_join(message)
            return

        has_media = (
            (hasattr(message, "photo") and message.photo) or
            (hasattr(message, "photos") and message.photos) or
            (hasattr(message, "document") and message.document) or
            (hasattr(message, "voice") and message.voice)
        )
        has_contact = hasattr(message, "contact") and message.contact

        if has_media or has_contact:
            await _handle_media(bot, message, bale_id)
            return

        from handlers import start, order, account, info, staff
        from handlers.admin import panel as adm

        if text == "پنل ادمین" and bale_id not in SUPER_ADMIN_IDS:
            await message.reply("دسترسی ندارید.")
            return

        routes = {
            "/start":             start.cmd_start,
            "ثبت سفارش جدید":    order.cmd_new_order,
            "حساب کاربری":        account.cmd_account,
            "اخبار و اطلاعیه":    info.cmd_news,
            "روزنامه":            info.cmd_newspaper,
            "کاتالوگ و اطلاعات": info.cmd_catalog,
            "سوالات متداول":      info.cmd_faq,
            "پشتیبانی":           info.cmd_support,
            "پرداخت اقساط":       order.cmd_pay_installment,
            "ارتباط با ما":       info.cmd_contact,
            "درباره ما":          info.cmd_about,
            "پرداخت اقساط":       order.cmd_pay_installment,
            "پنل کارکنان":        staff.cmd_staff,
            "پنل مالی":           adm.cmd_finance_panel,
            "پنل ادمین":          adm.cmd_admin_panel,
            "منوی اصلی":          start.cmd_main_menu,
        }

        if text in routes:
            await routes[text](bot, message)
            return

        await _handle_state(bot, message, bale_id)

    except Exception:
        log.error(f"خطا در on_message:\n{traceback.format_exc()}")


async def _handle_media(bot, message, bale_id):
    from database.db import get_state
    state, d = get_state(bale_id)

    has_contact = hasattr(message, "contact") and message.contact
    if state == "W_PHONE" and has_contact:
        from handlers.start import state_phone
        await state_phone(bot, message)
        return

    if state == "W_RECEIPT":
        from handlers.order import handle_receipt_photo
        await handle_receipt_photo(bot, message)
    elif state == "W_TICKET_MSG":
        from handlers.info import state_ticket_message
        await state_ticket_message(bot, message)
    elif state == "W_STAFF_REPORT":
        from handlers.staff import state_staff_report
        await state_staff_report(bot, message)
    elif state == "A_CATALOG_FILE":
        from handlers.admin import panel as adm
        await adm.state_catalog_file(bot, message)
    elif state == "W_INST_RECEIPT":
        from handlers.order import handle_inst_receipt
        await handle_inst_receipt(bot, message)
    elif state == "W_CHECK_ID_CARD":
        from handlers.order import handle_check_id_card
        await handle_check_id_card(bot, message)
    elif state == "W_CHECK_FILE":
        from handlers.order import handle_check_file
        await handle_check_file(bot, message)
    elif state == "A_NP_FILE":
        from handlers.admin import panel as adm
        await adm.state_newspaper_file(bot, message)
    elif state == "A_TASK_BODY":
        from handlers.admin import panel as adm
        await adm.state_task_body(bot, message)


async def _handle_state(bot, message, bale_id):
    from database.db import get_state
    from handlers import start, order, info, staff
    from handlers.admin import panel as adm

    state, _ = get_state(bale_id)
    if not state: return

    state_map = {
        "W_NAME":          start.state_name,
        "W_PHONE":         start.state_phone,
        "W_QUANTITY":      order.state_quantity,
        "W_INFO_1":        order.state_info_1,
        "W_INFO_2":        order.state_info_2,
        "W_INFO_3":        order.state_info_3,
        "W_INFO_4":        order.state_info_4,
        "W_INFO_5":        order.state_info_5,
        "W_INFO_6":        order.state_info_6,
        "W_INFO_7":        order.state_info_7,
        "W_INFO_8":        order.state_info_8,
        "W_TICKET_MSG":    info.state_ticket_message,
        "W_STAFF_REPORT":  staff.state_staff_report,
        "W_TRACKING_CODE": staff.state_tracking_code,
        "W_PAY_TYPE":      order.cb_payment_type,
        "W_ORDER_NOTE":    order.handle_order_note,
        "W_INST_AMOUNT":   order.state_inst_amount,
        "W_WH_STOCK":      staff.state_wh_stock,
        "A_REJECT_REASON": adm.state_reject_reason,
        "A_ADD_STAFF_ID":  adm.state_add_staff_id,
        "A_DISCOUNT_VAL":  adm.state_discount_val,
        "A_NEWS_TITLE":    adm.state_news_title,
        "A_NEWS_BODY":     adm.state_news_body,
        "A_NP_TITLE":      adm.state_newspaper_title,
        "A_NP_URL":        adm.state_newspaper_url,
        "A_FAQ_Q":         adm.state_faq_question,
        "A_FAQ_A":         adm.state_faq_answer,
        "A_BROADCAST":     adm.state_broadcast,
        "A_EDIT_SETTING":  adm.state_edit_setting,
        "A_ADD_PROD_1":    adm.state_add_product,
        "A_ADD_PROD_2":    adm.state_add_product,
        "A_ADD_PROD_3":    adm.state_add_product,
        "A_ADD_PROD_4":    adm.state_add_product,
        "A_ADD_PROD_5":    adm.state_add_product,
        "A_ADD_PROD_6":    adm.state_add_product,
        "A_ADD_PROD_7":    adm.state_add_product,
        "A_ADD_PROD_8":    adm.state_add_product,
        "A_EDIT_PRICE":    adm.state_edit_price,
        "A_EDIT_STOCK":    adm.state_edit_stock,
        "A_CATALOG_TITLE": adm.state_catalog_title,
        "A_CATALOG_URL":        adm.state_catalog_url,
        "A_STAFF_NEWS_TITLE":   adm.state_staff_news_title,
        "A_STAFF_NEWS_BODY":    adm.state_staff_news_body,
        "W_ROLE_CONFIRM":      start.cb_role,
        "W_ROLE_OTHER":        start.state_role_other,
        "A_TASK_TITLE":        adm.state_task_title,
        "A_TASK_BODY":         adm.state_task_body,
        "W_CHECK_NATIONAL_ID": order.state_check_national_id,
        "A_FIN_REJECT":        adm.state_fin_reject,
    }
    handler = state_map.get(state)
    if handler: await handler(bot, message)


@bot.event
async def on_callback(callback: CallbackQuery):
    try:
        if not callback.from_user: return
        data = callback.data or ""
        bale_id = int(callback.from_user.user_id)

        # ── cb_joined جداست — خودش چک می‌کنه ──
        if data == "cb_joined":
            from handlers.start import cb_joined
            await cb_joined(bot, callback)
            try: await callback.answer()
            except: pass
            return

        # ── همه callback های دیگه — چک عضویت ──
        if not await _is_member(bale_id):
            await _ask_join(callback, is_callback=True)
            try: await callback.answer()
            except: pass
            return

        from handlers import start, order, info, staff
        from handlers.admin import panel as adm

        if   data.startswith("cb_role_"):                              await start.cb_role(bot, callback)
        elif data in ("cb_role_confirm","cb_role_change"):                await start.cb_role(bot, callback)
        elif data in ("cb_cat_xbone","cb_cat_xpatch","cb_order_back"): await order.cb_category(bot, callback)
        elif data in ("cb_sub_xpatch","cb_sub_crosslinked"):           await order.cb_xpatch_type(bot, callback)
        elif data.startswith("cb_particle_"):                          await order.cb_particle(bot, callback)
        elif data.startswith("cb_vol_"):                               await order.cb_volume(bot, callback)
        elif data == "cb_add_more":                                    await order.cb_add_more(bot, callback)
        elif data == "cb_confirm_order":                               await order.cb_confirm_order(bot, callback)
        elif data == "cb_final_confirm":                               await order.cb_final_confirm(bot, callback)
        elif data == "cb_cancel_order":                                await order.cb_cancel_order(bot, callback)
        # نوع پرداخت
        elif data in ("cb_pay_full","cb_pay_installment","cb_pay_inst_zero","cb_pay_check","cb_pay_back"): await order.cb_payment_type(bot, callback)
        # توضیح سفارش
        elif data == "cb_no_note":                                     await order.cb_no_note(bot, callback)
        # پرداخت قسط
        elif data.startswith("inst_pay_"):                             await order.cb_inst_pay_select(bot, callback)
        elif data.startswith("inst_approve_"):                         await adm.cb_installment_payment(bot, callback)
        elif data.startswith("inst_reject_"):                          await adm.cb_installment_payment(bot, callback)
        elif data in ("cb_clock_in","cb_clock_out","cb_attendance",
                      "cb_staff_news","cb_staff_tasks") or \
             data.startswith("cb_snews_") or \
             data.startswith("cb_task_"):                              await staff.cb_staff_type(bot, callback)
        # دوره اکسل
        elif data.startswith("excel_orders_"):                         await adm.cb_excel_orders(bot, callback)
        elif data == "excel_customers":                                await adm.cb_excel_customers(bot, callback)
        # سفارشات
        elif data.startswith("cb_news_"):                              await info.cb_news_item(bot, callback)
        elif data.startswith("cb_np_"):                                await info.cb_newspaper_item(bot, callback)
        elif data.startswith("cb_catalog_"):                           await info.cb_catalog_item(bot, callback)
        elif data.startswith("cb_faq_"):                               await info.cb_faq_item(bot, callback)
        elif data.startswith("cb_sup_"):                               await info.cb_support_subject(bot, callback)
        elif data.startswith("wh_"):                                   await staff.cb_warehouse(bot, callback)
        elif data.startswith("cb_staff_"):                             await staff.cb_staff_type(bot, callback)
        elif data == "cb_check_confirm":                               await order.cb_check_confirm(bot, callback)
        elif data.startswith("fin_approve_") or data.startswith("fin_need_check_") or \
             data.startswith("fin_reject_") or data.startswith("fin_final_"): await adm.route_admin_callback(bot, callback)
        elif data.startswith("admin_check"):                               await adm.route_admin_callback(bot, callback)
        elif data.startswith("approve_"):                                  await adm.cb_approve(bot, callback)
        elif data.startswith("reject_"):                               await adm.cb_reject_start(bot, callback)
        elif data.startswith("rep_"):                                     await adm.cb_report_period(bot, callback)
        elif data.startswith("admin_staff_task_") or data.startswith("admin_task_list_"): await adm.route_admin_callback(bot, callback)
        elif data.startswith("admin_"):                                    await adm.route_admin_callback(bot, callback)

        try: await callback.answer()
        except: pass

    except Exception:
        log.error(f"خطا در on_callback:\n{traceback.format_exc()}")


if __name__ == "__main__":
    bot.run()

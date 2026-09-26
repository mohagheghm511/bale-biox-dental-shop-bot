from utils.date_utils import to_jalali, now_jalali, today_jalali
from database.db import (
    get_user, get_product, create_order, get_order, get_user_orders,
    update_order, get_setting, get_state, set_state, clear_state,
    calc_discount, decrease_stock,
    get_products_by_category, get_particle_sizes, get_volume_sizes,
    create_check_doc, update_check_doc, get_check_doc, get_finance_staff
)
from utils.keyboards import (
    order_category_keyboard, xpatch_type_keyboard, particle_size_keyboard,
    volume_size_keyboard, cart_keyboard, invoice_keyboard,
    receipt_admin_keyboard, main_kb,
    check_confirm_keyboard, finance_check_keyboard, finance_check_final_keyboard
)

STATUS_FA = {
    "pending_payment": "در انتظار پرداخت",
    "receipt_sent":    "فیش در حال بررسی",
    "approved":        "تایید شده",
    "rejected":        "رد شده",
    "shipped":         "ارسال شده",
}

INFO_STEPS = [
    ("real_name",    "W_INFO_1", "نام حقیقی/حقوقی خود را وارد کنید:"),
    ("national_id",  "W_INFO_2", "کد ملی یا شناسه ملی را وارد کنید:"),
    ("postal_code",  "W_INFO_3", "کد پستی را وارد کنید (۱۰ رقم):"),
    ("birth_date",   "W_INFO_4", "تاریخ تولد را وارد کنید:\nمثال: 1360/05/20"),
    ("medical_code", "W_INFO_5", "کد نظام پزشکی را وارد کنید:"),
    ("address",      "W_INFO_6", "آدرس کامل را وارد کنید:"),
    ("landline",     "W_INFO_7", "تلفن ثابت را وارد کنید:\nمثال: 02112345678"),
    ("phone",        "W_INFO_8", "شماره همراه را وارد کنید:\nمثال: 09121234567"),
]


def _note_keyboard():
    from bale import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("توضیحی ندارم", callback_data="cb_no_note"), row=1)
    return kb

async def cmd_new_order(bot, message):
    bale_id = int(message.author.user_id)
    user = get_user(bale_id)
    if not user or not user["full_name"]:
        await message.reply("لطفاً ابتدا /start را بزنید.")
        return
    set_state(bale_id, "W_CAT", {"cart": []})
    await message.reply("ثبت سفارش جدید\n\nنوع محصول را انتخاب کنید:", components=order_category_keyboard())

# ── مرحله ۱: انتخاب دسته ──
async def cb_category(bot, callback):
    bale_id = int(callback.from_user.user_id)
    data = callback.data
    _, d = get_state(bale_id)
    d = d or {}

    if data == "cb_order_back":
        # برگشت به منوی دسته‌بندی
        set_state(bale_id, "W_CAT", d)
        await callback.message.edit("نوع محصول را انتخاب کنید:", components=order_category_keyboard())
        return

    if data == "cb_cat_xbone":
        d["category"] = "xbone"
        d["sub_category"] = "xbone"
        sizes = get_particle_sizes("xbone")
        set_state(bale_id, "W_PARTICLE", d)
        await callback.message.edit(
            "PARTICLE SIZE را انتخاب کنید:",
            components=particle_size_keyboard(sizes)
        )

    elif data == "cb_cat_xpatch":
        d["category"] = "xpatch"
        set_state(bale_id, "W_XPATCH_TYPE", d)
        await callback.message.edit("ممبران\n\nنوع ممبران را انتخاب کنید:", components=xpatch_type_keyboard())

# ── انتخاب نوع X Patch ──
async def cb_xpatch_type(bot, callback):
    bale_id = int(callback.from_user.user_id)
    data = callback.data
    _, d = get_state(bale_id)
    d = d or {}

    if data == "cb_order_back":
        set_state(bale_id, "W_CAT", d)
        await callback.message.edit("نوع محصول را انتخاب کنید:", components=order_category_keyboard())
        return

    sub = "xpatch" if data == "cb_sub_xpatch" else "crosslinked"
    label = "X Patch" if sub == "xpatch" else "Cross Linked X Patch"
    d["sub_category"] = sub
    sizes = get_particle_sizes(sub)
    set_state(bale_id, "W_PARTICLE", d)
    await callback.message.edit(
        f"{label}\n\nضخامت را انتخاب کنید:",
        components=particle_size_keyboard(sizes)
    )

# ── مرحله ۲: انتخاب particle/ضخامت ──
async def cb_particle(bot, callback):
    bale_id = int(callback.from_user.user_id)
    data = callback.data
    _, d = get_state(bale_id)
    d = d or {}

    if data == "cb_order_back":
        cat = d.get("category")
        if cat == "xbone":
            set_state(bale_id, "W_CAT", d)
            await callback.message.edit("نوع محصول را انتخاب کنید:", components=order_category_keyboard())
        else:
            set_state(bale_id, "W_XPATCH_TYPE", d)
            await callback.message.edit("نوع ممبران را انتخاب کنید:", components=xpatch_type_keyboard())
        return

    idx = int(data.replace("cb_particle_", ""))
    sub = d.get("sub_category", "xbone")
    sizes = get_particle_sizes(sub)
    if idx >= len(sizes):
        return
    particle = sizes[idx]
    d["particle_size"] = particle
    products = get_volume_sizes(sub, particle)
    set_state(bale_id, "W_VOLUME", d)

    cat_label = "X Bone" if sub == "xbone" else ("X Patch" if sub == "xpatch" else "Cross Linked X Patch")
    await callback.message.edit(
        f"{cat_label} | {particle}\n\nسایز/حجم را انتخاب کنید:",
        components=volume_size_keyboard(products)
    )

# ── مرحله ۳: انتخاب حجم/سایز ──
async def cb_volume(bot, callback):
    bale_id = int(callback.from_user.user_id)
    data = callback.data
    _, d = get_state(bale_id)
    d = d or {}

    if data == "cb_order_back":
        sub = d.get("sub_category", "xbone")
        sizes = get_particle_sizes(sub)
        set_state(bale_id, "W_PARTICLE", d)
        label = "PARTICLE SIZE" if sub == "xbone" else "ضخامت"
        await callback.message.edit(f"{label} را انتخاب کنید:", components=particle_size_keyboard(sizes))
        return

    pid = int(data.replace("cb_vol_", ""))
    prod = get_product(pid)
    if not prod or prod["stock"] <= 0:
        await callback.message.edit("موجودی این محصول تمام شده.")
        return

    d["pid"] = pid
    set_state(bale_id, "W_QUANTITY", d)
    await callback.message.edit(
        f"محصول انتخاب شده:\n"
        f"کد: {prod['catalog_code']}\n"
        f"{prod['name']}\n"
        f"قیمت: {prod['price']:,} تومان\n"
        f"موجودی: {prod['stock']} عدد\n\n"
        f"تعداد مورد نیاز را به عدد انگلیسی وارد کنید:"
    )

# ── مرحله ۴: تعداد ──
async def state_quantity(bot, message):
    bale_id = int(message.author.user_id)
    text = (message.content or "").strip()
    if not text.isdigit() or int(text) <= 0:
        await message.reply("یک عدد صحیح مثبت وارد کنید:")
        return
    qty = int(text)
    _, d = get_state(bale_id)
    d = d or {}
    pid = d.get("pid")
    prod = get_product(pid)
    if not prod:
        await message.reply("خطا. /start را بزنید.")
        return
    if qty > prod["stock"]:
        await message.reply(f"موجودی کافی نیست. حداکثر {prod['stock']} عدد:")
        return

    cart = d.get("cart", [])
    cart.append({
        "pid": pid, "catalog_code": prod["catalog_code"],
        "name": prod["name"], "size": prod["volume_size"],
        "qty": qty, "unit_price": prod["price"],
        "subtotal": prod["price"] * qty
    })
    d["cart"] = cart
    set_state(bale_id, "W_CART", d)

    total = sum(i["subtotal"] for i in cart)
    txt = "سبد خرید:\n━━━━━━━━━━━━━━━\n"
    for item in cart:
        txt += f"• {item['catalog_code']} | {item['size']} × {item['qty']} = {item['subtotal']:,} ت\n"
    txt += f"━━━━━━━━━━━━━━━\nجمع: {total:,} تومان"
    await message.reply(txt, components=cart_keyboard())

async def cb_add_more(bot, callback):
    bale_id = int(callback.from_user.user_id)
    _, d = get_state(bale_id)
    set_state(bale_id, "W_CAT", d or {})
    await callback.message.edit("نوع محصول بعدی:", components=order_category_keyboard())

# ── تایید سفارش → دریافت اطلاعات هویتی ──
async def cb_confirm_order(bot, callback):
    bale_id = int(callback.from_user.user_id)
    _, d = get_state(bale_id)
    d = d or {}
    cart = d.get("cart", [])
    if not cart:
        await callback.message.edit("سبد خرید خالی است.")
        return

    total = sum(i["subtotal"] for i in cart)
    user = get_user(bale_id)
    discount = calc_discount(user["role"] or "", total)
    final = total - discount
    d.update({"total": total, "discount": discount, "final": final})
    set_state(bale_id, "W_INFO_1", d)

    txt = "خلاصه سفارش:\n━━━━━━━━━━━━━━━\n"
    for item in cart:
        txt += f"• {item['catalog_code']} | {item['size']} × {item['qty']} = {item['subtotal']:,} ت\n"
    txt += f"━━━━━━━━━━━━━━━\nجمع کل: {total:,} تومان\n"
    if discount > 0:
        txt += f"تخفیف: {discount:,} تومان\n"
    txt += f"مبلغ نهایی: {final:,} تومان\n\n"
    txt += "━━━━━━━━━━━━━━━\nتکمیل اطلاعات هویتی (اجباری)\n\n"
    txt += INFO_STEPS[0][2]
    await callback.message.edit(txt)

async def _handle_info_step(bot, message, step_index):
    bale_id = int(message.author.user_id)
    text = (message.content or "").strip()
    _, d = get_state(bale_id)
    d = d or {}
    field_name = INFO_STEPS[step_index][0]

    if step_index == 2:
        if not (text.isdigit() and len(text) == 10):
            await message.reply("کد پستی باید ۱۰ رقم باشد:"); return
    elif step_index == 6:
        cleaned = text.replace("-","").replace(" ","")
        if not (cleaned.isdigit() and len(cleaned) >= 8):
            await message.reply("شماره تلفن ثابت نامعتبر است:"); return
        text = cleaned
    elif step_index == 7:
        cleaned = text.replace("-","").replace(" ","").replace("+","")
        if cleaned.startswith("0098"): cleaned = "0" + cleaned[4:]
        elif cleaned.startswith("98"): cleaned = "0" + cleaned[2:]
        if not (cleaned.startswith("09") and len(cleaned)==11 and cleaned.isdigit()):
            await message.reply("شماره موبایل نامعتبر است. مثال: 09121234567"); return
        text = cleaned

    d[field_name] = text
    next_step = step_index + 1
    if next_step < len(INFO_STEPS):
        set_state(bale_id, INFO_STEPS[next_step][1], d)
        await message.reply(f"ثبت شد.\n\n{INFO_STEPS[next_step][2]}")
    else:
        set_state(bale_id, "W_INVOICE_CONFIRM", d)
        await _show_invoice(bot, message, bale_id, d)

async def _show_invoice(bot, message, bale_id, d):
    cart = d.get("cart", [])
    total, discount, final = d.get("total",0), d.get("discount",0), d.get("final",0)
    txt = (
        "پیش‌فاکتور\n━━━━━━━━━━━━━━━\n"
        f"نام: {d.get('real_name','-')}\n"
        f"کد ملی: {d.get('national_id','-')}\n"
        f"کد پستی: {d.get('postal_code','-')}\n"
        f"تاریخ تولد: {d.get('birth_date','-')}\n"
        f"کد نظام پزشکی: {d.get('medical_code','-')}\n"
        f"آدرس: {d.get('address','-')}\n"
        f"تلفن ثابت: {d.get('landline','-')}\n"
        f"موبایل: {d.get('phone','-')}\n"
        "━━━━━━━━━━━━━━━\n"
    )
    for item in cart:
        txt += f"• {item['catalog_code']} | {item['size']} × {item['qty']} = {item['subtotal']:,} ت\n"
    txt += f"━━━━━━━━━━━━━━━\nجمع کل: {total:,} تومان\n"
    if discount > 0: txt += f"تخفیف: {discount:,} تومان\n"
    txt += f"مبلغ نهایی: {final:,} تومان"
    await message.reply(txt, components=invoice_keyboard())

async def cb_final_confirm(bot, callback):
    bale_id = int(callback.from_user.user_id)
    _, d = get_state(bale_id)
    d = d or {}
    cart = d.get("cart", [])
    from database.db import update_user as _uu
    fields = {f: d[f] for f, _, _ in INFO_STEPS if f in d and d[f]}
    if fields: _uu(bale_id, **fields)

    order_num = create_order(bale_id, cart, d.get("total",0), d.get("discount",0), d.get("final",0))
    for item in cart:
        decrease_stock(item["pid"], item["qty"])
    d["order_num"] = order_num
    set_state(bale_id, "W_PAY_TYPE", d)

    from utils.keyboards import payment_type_keyboard
    await callback.message.edit(
        f"سفارش {order_num} ثبت شد!\n\n"
        f"مبلغ نهایی: {d['final']:,} تومان\n\n"
        f"نوع پرداخت را انتخاب کنید:",
        components=payment_type_keyboard()
    )

async def cb_cancel_order(bot, callback):
    bale_id = int(callback.from_user.user_id)
    clear_state(bale_id)
    from bot import SUPER_ADMIN_IDS
    from database.db import get_staff_roles
    roles = get_staff_roles(bale_id)
    await callback.message.edit("سفارش لغو شد.")
    await bot.send_message(bale_id, "منوی اصلی:", components=main_kb(
        is_admin=bale_id in SUPER_ADMIN_IDS, is_staff=len(roles)>0, is_warehouse="warehouse" in roles))

async def handle_receipt_photo(bot, message):
    bale_id = int(message.author.user_id)
    state, d = get_state(bale_id)
    if state != "W_RECEIPT": return
    d = d or {}
    order_num = d.get("order_num")
    if not order_num: return

    file_id = None; ftype = "photo"
    if hasattr(message,"photo") and message.photo: file_id = message.photo.file_id
    elif hasattr(message,"photos") and message.photos: file_id = message.photos[-1].file_id
    elif hasattr(message,"document") and message.document: file_id = message.document.file_id; ftype = "document"
    if not file_id:
        await message.reply("فایل دریافت نشد. دوباره ارسال کنید."); return

    update_order(order_num, status="receipt_sent", receipt_file_id=file_id, receipt_type=ftype)

    # اگه اقساطی بود ثبت قسط
    if d.get("pay_type") in ("installment", "inst_zero"):
        from datetime import datetime, timedelta
        from database.db import create_installment
        final = d.get("final", 0)
        prepay = d.get("prepay", int(final * 50 / 100))
        remaining = final - prepay
        due_date = d.get("due_date", (datetime.now() + timedelta(days=45)).strftime("%Y/%m/%d"))
        create_installment(order_num, bale_id, final, prepay, remaining, due_date)

    set_state(bale_id, "W_ORDER_NOTE", {"order_num": order_num, "pay_type": d.get("pay_type","full")})
    await message.reply(
        f"فیش دریافت شد!\nشماره سفارش: {order_num}\n\n"
        "آیا توضیحاتی برای سفارش دارید؟\n"
        "(مثل: رنگ خاص، زمان تحویل و...)",
        components=_note_keyboard()
    )

    from bot import SUPER_ADMIN_IDS
    import json
    user = get_user(bale_id)
    order = get_order(order_num)
    items = json.loads(order["items"])
    items_txt = "\n".join(f"• {i['catalog_code']} | {i['size']} × {i['qty']}" for i in items)
    pay_type = d.get("pay_type", "full")
    pay_label = {"full": "پرداخت کامل", "installment": "اقساطی ۵۰٪", "inst_zero": "اقساطی بدون پیش‌پرداخت"}.get(pay_type, "نامشخص")
    caption = (
        f"فیش پرداخت جدید\n━━━━━━━━━━━━━━━\n"
        f"نوع پرداخت: {pay_label}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"نام: {user['full_name']}\n"
        f"موبایل: {user['phone']}\n"
        f"سمت: {user['role']}\n"
        f"کد ملی: {user['national_id'] or '-'}\n"
        f"آدرس: {user['address'] or '-'}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"سفارش: {order_num}\n{items_txt}\n"
        f"━━━━━━━━━━━━━━━\nمبلغ: {order['final_amount']:,} تومان"
    )
    kb = receipt_admin_keyboard(order_num)
    from bale import InputFile
    for aid in SUPER_ADMIN_IDS:
        try:
            if ftype == "document":
                await bot.send_document(aid, InputFile(file_id), caption=caption, components=kb)
            else:
                await bot.send_photo(aid, InputFile(file_id), caption=caption, components=kb)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"خطا در ارسال فیش به ادمین {aid}: {e}")

async def state_info_1(bot, message): await _handle_info_step(bot, message, 0)
async def state_info_2(bot, message): await _handle_info_step(bot, message, 1)
async def state_info_3(bot, message): await _handle_info_step(bot, message, 2)
async def state_info_4(bot, message): await _handle_info_step(bot, message, 3)
async def state_info_5(bot, message): await _handle_info_step(bot, message, 4)
async def state_info_6(bot, message): await _handle_info_step(bot, message, 5)
async def state_info_7(bot, message): await _handle_info_step(bot, message, 6)
async def state_info_8(bot, message): await _handle_info_step(bot, message, 7)

# ── انتخاب نوع پرداخت ────────────────────────────────────
async def cb_payment_type(bot, callback):
    bale_id = int(callback.from_user.user_id)
    data = callback.data
    _, d = get_state(bale_id)
    d = d or {}

    if data == "cb_pay_full":
        d["pay_type"] = "full"
        set_state(bale_id, "W_RECEIPT", d)
        card = get_setting("bank_card", "")
        owner = get_setting("bank_owner", "")
        pay_text = get_setting("payment_text", "لطفاً مبلغ را واریز کنید.")
        await callback.message.edit(
            f"سفارش {d.get('order_num')} ثبت شد!\n\n{pay_text}\n\n"
            f"شماره کارت: {card}\nبه نام: {owner}\n"
            f"مبلغ: {d['final']:,} تومان\n\n"
            f"پس از واریز، تصویر فیش را ارسال کنید."
        )

    elif data == "cb_pay_installment":
        d["pay_type"] = "installment"
        final = d.get("final", 0)
        prepay = int(final * 50 / 100)
        remaining = final - prepay
        d["prepay"] = prepay
        d["remaining_inst"] = remaining
        set_state(bale_id, "W_RECEIPT", d)

        from datetime import datetime, timedelta
        due = (datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d")
        d["due_date"] = due

        card = get_setting("bank_card", "")
        owner = get_setting("bank_owner", "")
        await callback.message.edit(
            f"پرداخت اقساطی انتخاب شد.\n\n"
            f"مبلغ کل: {final:,} تومان\n"
            f"پیش‌پرداخت (۵۰٪): {prepay:,} تومان\n"
            f"مانده: {remaining:,} تومان\n"
            f"سررسید: {to_jalali(due)}\n\n"
            f"شماره کارت: {card}\nبه نام: {owner}\n\n"
            f"لطفاً {prepay:,} تومان واریز کنید و تصویر فیش را ارسال کنید."
        )


    elif data == "cb_pay_inst_zero":
        d["pay_type"] = "inst_zero"
        final = d.get("final", 0)
        d["prepay"] = 0
        d["remaining_inst"] = final
        set_state(bale_id, "W_RECEIPT", d)
        from datetime import datetime, timedelta
        due = (datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d")
        d["due_date"] = due
        set_state(bale_id, "W_RECEIPT", d)
        card = get_setting("bank_card", "")
        owner = get_setting("bank_owner", "")
        await callback.message.edit(
            f"اقساطی بدون پیش‌پرداخت انتخاب شد.\n\n"
            f"مبلغ کل: {final:,} تومان\n"
            f"مانده: {final:,} تومان\n"
            f"سررسید: {to_jalali(due)}\n\n"
            f"شماره کارت: {card}\nبه نام: {owner}\n\n"
            f"لطفاً تصویر فیش را ارسال کنید.\n"
            f"(تأیید این نوع پرداخت منوط به تأیید ادمین است)"
        )


    elif data == "cb_pay_check":
        # چک/تعهدنامه — شروع مراحل
        d["pay_type"] = "check"
        set_state(bale_id, "W_CHECK_NATIONAL_ID", d)
        await callback.message.edit(
            "چک / تعهدنامه انتخاب شد.\n\n"
            "⚠️ توجه: کد ملی وارد شده حتماً باید با نام صاحب حساب و مدارک ارسالی مطابقت داشته باشد.\n\n"
            "کد ملی خود را وارد کنید:"
        )

    elif data == "cb_pay_back":
        # بازگشت به انتخاب نوع پرداخت
        from utils.keyboards import payment_type_keyboard
        await callback.message.edit("نوع پرداخت را انتخاب کنید:", components=payment_type_keyboard())


# ── چک/تعهدنامه ──────────────────────────────────────────
async def state_check_national_id(bot, message):
    """دریافت کد ملی برای چک/تعهدنامه"""
    bale_id = int(message.author.user_id)
    state, d = get_state(bale_id)
    if state != "W_CHECK_NATIONAL_ID": return
    d = d or {}
    nid = (message.content or "").strip().replace("-","").replace(" ","")
    if not (nid.isdigit() and len(nid) == 10):
        await message.reply(
            "⚠️ کد ملی نامعتبر است. باید ۱۰ رقم باشد:\nمثال: 1234567890"
        )
        return
    d["check_national_id"] = nid
    set_state(bale_id, "W_CHECK_ID_CARD", d)
    await message.reply(
        f"کد ملی {nid} ثبت شد.\n\n"
        "📷 لطفاً تصویر واضح کارت ملی خود را ارسال کنید:"
    )


async def handle_check_id_card(bot, message):
    """دریافت عکس کارت ملی"""
    bale_id = int(message.author.user_id)
    state, d = get_state(bale_id)
    if state != "W_CHECK_ID_CARD": return
    d = d or {}

    file_id = None
    if hasattr(message,"photo") and message.photo: file_id = message.photo.file_id
    elif hasattr(message,"photos") and message.photos: file_id = message.photos[-1].file_id
    elif hasattr(message,"document") and message.document: file_id = message.document.file_id
    if not file_id:
        await message.reply("تصویر دریافت نشد. لطفاً دوباره ارسال کنید.")
        return

    d["check_id_card_file"] = file_id
    set_state(bale_id, "W_CHECK_CONFIRM", d)

    # نمایش متن تعهدنامه
    commitment = get_setting("commitment_text", "اینجانب تعهد می‌دهم که کلیه اقلام سفارش داده شده را در موعد مقرر تسویه نمایم.")
    await message.reply(
        f"متن تعهدنامه:\n━━━━━━━━━━━━━━━\n{commitment}\n━━━━━━━━━━━━━━━\n\n"
        "در صورت موافقت دکمه «تأیید کردم» را بزنید:",
        components=check_confirm_keyboard()
    )


async def cb_check_confirm(bot, callback):
    """تأیید تعهدنامه و ارسال مدارک برای ادمین و مالی"""
    bale_id = int(callback.from_user.user_id)
    _, d = get_state(bale_id)
    d = d or {}

    order_num = d.get("order_num")
    national_id = d.get("check_national_id")
    id_card_file = d.get("check_id_card_file")

    # ذخیره در دیتابیس
    create_check_doc(order_num, bale_id, national_id, id_card_file)
    update_order(order_num, status="check_pending")

    set_state(bale_id, "W_ORDER_NOTE", {"order_num": order_num, "pay_type": "check"})
    await callback.message.edit(
        f"مدارک شما دریافت شد.\nشماره سفارش: {order_num}\n\n"
        "در انتظار بررسی توسط واحد مالی...\n\n"
        "آیا توضیحاتی برای سفارش دارید؟",
        components=_note_keyboard()
    )

    # ارسال به ادمین اصلی و مسئولین مالی
    from bot import SUPER_ADMIN_IDS
    from bale import InputFile
    import json
    user = get_user(bale_id)
    order = get_order(order_num)
    items = json.loads(order["items"])
    items_txt = "\n".join(f"• {i['catalog_code']} | {i['size']} × {i['qty']}" for i in items)

    caption = (
        f"مدارک چک/تعهدنامه جدید\n━━━━━━━━━━━━━━━\n"
        f"نام: {user['full_name']}\n"
        f"موبایل: {user['phone']}\n"
        f"سمت: {user['role']}\n"
        f"کد ملی: {national_id}\n"
        f"آدرس: {user['address'] or '-'}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"سفارش: {order_num}\n{items_txt}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"مبلغ: {order['final_amount']:,} تومان"
    )
    kb = finance_check_keyboard(order_num)
    recipients = list(set(list(SUPER_ADMIN_IDS) + get_finance_staff()))
    for rid in recipients:
        try:
            await bot.send_photo(rid, InputFile(id_card_file), caption=caption, components=kb)
        except Exception as e:
            import logging; logging.getLogger(__name__).error(f"خطا ارسال مدارک: {e}")


async def handle_check_file(bot, message):
    """دریافت فایل چک/سفته از کاربر"""
    bale_id = int(message.author.user_id)
    state, d = get_state(bale_id)
    if state != "W_CHECK_FILE": return
    d = d or {}

    file_id = None
    if hasattr(message,"photo") and message.photo: file_id = message.photo.file_id
    elif hasattr(message,"photos") and message.photos: file_id = message.photos[-1].file_id
    elif hasattr(message,"document") and message.document: file_id = message.document.file_id
    if not file_id:
        await message.reply("فایل دریافت نشد. دوباره ارسال کنید.")
        return

    order_num = d.get("order_num")
    update_check_doc(order_num, check_file=file_id, status="check_received")
    clear_state(bale_id)
    await message.reply("چک/سفته دریافت شد. در انتظار تأیید نهایی واحد مالی...")

    # ارسال به مالی و ادمین
    from bot import SUPER_ADMIN_IDS
    from bale import InputFile
    user = get_user(bale_id)
    caption = (
        f"چک/سفته دریافت شد\n━━━━━━━━━━━━━━━\n"
        f"نام: {user['full_name']}\n"
        f"موبایل: {user['phone']}\n"
        f"سفارش: {order_num}"
    )
    kb = finance_check_final_keyboard(order_num)
    recipients = list(set(list(SUPER_ADMIN_IDS) + get_finance_staff()))
    for rid in recipients:
        try:
            await bot.send_photo(rid, InputFile(file_id), caption=caption, components=kb)
        except Exception as e:
            import logging; logging.getLogger(__name__).error(f"خطا ارسال چک: {e}")


# ── توضیحات سفارش ────────────────────────────────────────
async def handle_order_note(bot, message):
    """دریافت توضیحات بعد از ارسال فیش"""
    bale_id = int(message.author.user_id)
    state, d = get_state(bale_id)
    if state != "W_ORDER_NOTE":
        return
    d = d or {}
    note = (message.content or "").strip()
    d["order_note"] = note
    clear_state(bale_id)

    order_num = d.get("order_num", "")
    # ارسال توضیحات به انباردار
    if note:
        from bot import SUPER_ADMIN_IDS
        from database.db import get_all_staff, get_user as gu
        all_staff = get_all_staff()
        warehouse_ids = [s["bale_id"] for s in all_staff if s["staff_role"] == "warehouse"]
        user = gu(bale_id)
        notif = f"توضیحات سفارش {order_num}\nاز: {user['full_name']}\n\n{note}"
        for wid in warehouse_ids:
            try: await bot.send_message(wid, notif)
            except: pass

    from handlers.start import _make_main_kb
    await message.reply(
        f"سفارش شما ثبت شد.\nشماره سفارش: {order_num}\nدر حال بررسی...",
        components=_make_main_kb(bale_id)
    )


# ── پرداخت قسط ───────────────────────────────────────────
async def cmd_pay_installment(bot, message):
    bale_id = int(message.author.user_id)
    from database.db import get_user_installments, get_user
    installments = get_user_installments(bale_id)
    if not installments:
        await message.reply("قسط معوقه‌ای ندارید.")
        return

    from bale import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup()
    for i, inst in enumerate(installments):
        import json
        try:
            items = json.loads(inst["items"] or "[]")
            items_txt = ", ".join(f"{it['catalog_code']}" for it in items[:2])
        except:
            items_txt = inst["order_number"]
        kb.add(InlineKeyboardButton(
            f"{inst['order_number']} | مانده: {inst['remaining_amount']:,} ت",
            callback_data=f"inst_pay_{inst['order_number']}"
        ), row=i+1)
    await message.reply("اقساط معوق:", components=kb)


async def cb_inst_pay_select(bot, callback):
    bale_id = int(callback.from_user.user_id)
    order_num = callback.data.replace("inst_pay_", "")
    from database.db import get_installment
    inst = get_installment(order_num)
    if not inst:
        return
    set_state(bale_id, "W_INST_AMOUNT", {"order_num": order_num, "remaining": inst["remaining_amount"]})
    await callback.message.edit(
        f"سفارش: {order_num}\n"
        f"مبلغ کل: {inst['total_amount']:,} تومان\n"
        f"پرداخت شده: {inst['paid_amount']:,} تومان\n"
        f"مانده: {inst['remaining_amount']:,} تومان\n"
        f"سررسید: {to_jalali(inst['due_date'])}\n\n"
        f"مبلغی که می‌خواهید پرداخت کنید را وارد کنید (تومان):"
    )


async def state_inst_amount(bot, message):
    bale_id = int(message.author.user_id)
    text = (message.content or "").strip().replace(",", "").replace("،", "")
    if not text.isdigit() or int(text) <= 0:
        await message.reply("مبلغ نامعتبر است. عدد وارد کنید:")
        return
    amount = int(text)
    _, d = get_state(bale_id)
    d = d or {}
    remaining = d.get("remaining", 0)
    if amount > remaining:
        await message.reply(f"مبلغ بیشتر از مانده است. حداکثر {remaining:,} تومان:")
        return
    d["inst_pay_amount"] = amount
    set_state(bale_id, "W_INST_RECEIPT", d)
    card = get_setting("bank_card", "")
    owner = get_setting("bank_owner", "")
    await message.reply(
        f"مبلغ: {amount:,} تومان\n\n"
        f"شماره کارت: {card}\nبه نام: {owner}\n\n"
        f"تصویر فیش را ارسال کنید:"
    )


async def handle_inst_receipt(bot, message):
    bale_id = int(message.author.user_id)
    state, d = get_state(bale_id)
    if state != "W_INST_RECEIPT":
        return
    d = d or {}

    file_id = None; ftype = "photo"
    if hasattr(message, "photo") and message.photo: file_id = message.photo.file_id
    elif hasattr(message, "photos") and message.photos: file_id = message.photos[-1].file_id
    elif hasattr(message, "document") and message.document: file_id = message.document.file_id; ftype = "document"
    if not file_id:
        await message.reply("فایل دریافت نشد. دوباره ارسال کنید.")
        return

    from database.db import add_installment_payment, get_user, get_installment
    amount = d.get("inst_pay_amount", 0)
    order_num = d.get("order_num", "")
    payment_id_row = add_installment_payment(order_num, bale_id, amount, file_id, ftype)

    # پیدا کردن آخرین payment_id
    from database.db import get_conn
    conn = get_conn()
    pid = conn.execute("SELECT id FROM installment_payments WHERE order_number=? AND bale_id=? ORDER BY id DESC LIMIT 1",
                       (order_num, bale_id)).fetchone()
    conn.close()
    payment_id = pid["id"] if pid else 0

    clear_state(bale_id)
    await message.reply(f"فیش قسط دریافت شد!\nدر حال بررسی توسط ادمین...")

    # ارسال به ادمین
    from bot import SUPER_ADMIN_IDS
    from bale import InputFile
    user = get_user(bale_id)
    inst = get_installment(order_num)
    import json
    try:
        orders_row = __import__('database.db', fromlist=['get_order']).get_order(order_num)
        items = json.loads(orders_row["items"])
        items_txt = "\n".join(f"• {i['catalog_code']} | {i['size']} × {i['qty']}" for i in items)
    except:
        items_txt = order_num

    caption = (
        f"پرداخت قسط\n━━━━━━━━━━━━━━━\n"
        f"از: {user['full_name']} | {user['phone']}\n"
        f"سفارش: {order_num}\n{items_txt}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"مبلغ پرداختی: {amount:,} تومان\n"
        f"مانده قبلی: {inst['remaining_amount']:,} تومان"
    )
    from utils.keyboards import installment_approve_keyboard
    kb = installment_approve_keyboard(payment_id, order_num)
    for aid in SUPER_ADMIN_IDS:
        try:
            if ftype == "document":
                await bot.send_document(aid, InputFile(file_id), caption=caption, components=kb)
            else:
                await bot.send_photo(aid, InputFile(file_id), caption=caption, components=kb)
        except Exception as e:
            import logging; logging.getLogger(__name__).error(f"خطا ارسال فیش قسط: {e}")


async def cb_no_note(bot, callback):
    """کاربر توضیحی ندارم زد"""
    bale_id = int(callback.from_user.user_id)
    _, d = get_state(bale_id)
    d = d or {}
    order_num = d.get("order_num", "")
    clear_state(bale_id)

    from handlers.start import _make_main_kb
    await callback.message.edit(
        f"سفارش شما ثبت شد.\nشماره سفارش: {order_num}\nدر حال بررسی...",
    )
    await bot.send_message(bale_id, "منوی اصلی:", components=_make_main_kb(bale_id))

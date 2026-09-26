import sqlite3
import json
from datetime import datetime, timedelta

DB_NAME = "biox.db"

STAFF_ROLES = {
    "warehouse": "🏭 انباردار",
    "employee":  "👔 کارمند",
    "finance":   "💰 مسئول مالی",
}

def _now_str():
    """زمان فعلی به فرمت رشته"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY, value TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bale_id INTEGER UNIQUE NOT NULL,
        full_name TEXT, phone TEXT, role TEXT,
        real_name TEXT, national_id TEXT, postal_code TEXT,
        birth_date TEXT, medical_code TEXT, address TEXT, landline TEXT,
        is_banned INTEGER DEFAULT 0,
        joined_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS staff_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bale_id INTEGER NOT NULL, staff_role TEXT NOT NULL, added_by INTEGER,
        added_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(bale_id, staff_role)
    );
    CREATE TABLE IF NOT EXISTS user_states (
        bale_id INTEGER PRIMARY KEY, state TEXT, data TEXT DEFAULT '{}'
    );
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        sub_category TEXT NOT NULL DEFAULT '',
        particle_size TEXT NOT NULL DEFAULT '',
        volume_size TEXT NOT NULL DEFAULT '',
        catalog_code TEXT NOT NULL,
        name TEXT NOT NULL,
        price INTEGER NOT NULL DEFAULT 0,
        stock INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT UNIQUE NOT NULL,
        bale_id INTEGER NOT NULL, items TEXT NOT NULL,
        total_amount INTEGER NOT NULL, discount_amount INTEGER DEFAULT 0,
        final_amount INTEGER NOT NULL,
        status TEXT DEFAULT 'pending_payment',
        receipt_file_id TEXT, receipt_type TEXT DEFAULT 'photo',
        tracking_code TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, body TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP, is_active INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS newspaper (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, file_id TEXT, url TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP, is_active INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS catalog_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL, item_type TEXT NOT NULL,
        file_id TEXT, url TEXT, description TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP, is_active INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS faq (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL, answer TEXT NOT NULL,
        sort_order INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_code TEXT UNIQUE NOT NULL,
        bale_id INTEGER NOT NULL, subject TEXT NOT NULL,
        message_text TEXT, file_id TEXT, file_type TEXT,
        status TEXT DEFAULT 'open',
        admin_message_id INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS staff_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bale_id INTEGER NOT NULL, report_type TEXT,
        report_text TEXT, file_id TEXT, file_type TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS installments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT UNIQUE NOT NULL,
        bale_id INTEGER NOT NULL,
        total_amount INTEGER NOT NULL,
        paid_amount INTEGER DEFAULT 0,
        remaining_amount INTEGER NOT NULL,
        due_date TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS installment_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT NOT NULL,
        bale_id INTEGER NOT NULL,
        amount INTEGER NOT NULL,
        receipt_file_id TEXT,
        receipt_type TEXT DEFAULT 'photo',
        status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS check_docs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT NOT NULL,
        bale_id INTEGER NOT NULL,
        national_id TEXT,
        id_card_file TEXT,
        check_file TEXT,
        status TEXT DEFAULT 'pending',
        reject_reason TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS discounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role TEXT UNIQUE NOT NULL, discount_type TEXT NOT NULL, discount_value INTEGER NOT NULL
    );
    CREATE TABLE IF NOT EXISTS attendances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bale_id INTEGER NOT NULL,
        clock_in TEXT NOT NULL,
        clock_out TEXT,
        total_minutes INTEGER DEFAULT 0,
        date TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS staff_news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        is_active INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bale_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        body TEXT,
        file_id TEXT,
        file_type TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    defaults = {
        "channel_id": "@biox_official",
        "channel_required": "1",
        "channel_url": "https://ble.ir/biox_official",
        "bank_card": "6037-XXXX-XXXX-1234",
        "bank_owner": "شرکت BioX",
        "welcome_text": "به پلتفرم اطلاع‌رسانی شرکت دانش بنیان ایده زیست فارمد (BioX) خوش آمدید.\n\nبرای استفاده از خدمات لطفاً ابتدا وارد کانال شوید.",
        "payment_text": "لطفاً مبلغ را به شماره کارت زیر واریز کنید و تصویر فیش را ارسال نمایید.",
        "contact_text": "آدرس: تهران، منطقه۱۱\nایمیل: business@bioxenograft.com\nتلفن: 02166563801\nسایت: https://www.bioxenograft.com/",
        "commitment_text": "اینجانب تعهد می‌دهم که کلیه اقلام سفارش داده شده را در موعد مقرر تسویه نمایم.",
        "about_text": "شرکت دانش بنیان ایده زیست فارمد با نام تجاری BioX در سال ۱۴۰۲ تأسیس شد.",
        "support_admin_id": "",
    }
    for k, v in defaults.items():
        c.execute("INSERT OR IGNORE INTO settings (key,value) VALUES (?,?)", (k, v))

    # محصولات پیش‌فرض طبق PDF
    c.execute("SELECT COUNT(*) as cnt FROM products")
    if c.fetchone()["cnt"] == 0:
        _seed_products(c)

    c.execute("SELECT COUNT(*) as cnt FROM discounts")
    if c.fetchone()["cnt"] == 0:
        c.executemany("INSERT OR IGNORE INTO discounts (role,discount_type,discount_value) VALUES (?,?,?)", [
            ("🔬 جراح دندانپزشک", "percent", 10),
            ("🩺 دستیار دندانپزشک", "percent", 5),
        ])

    conn.commit(); conn.close()

def _seed_products(c):
    # X Bone — پودر استخوان
    # particle size 150-1000
    for code, vol in [("4016","0.3cc"),("4017","0.5cc"),("4018","1cc"),("4019","2cc"),("4020","5cc")]:
        c.execute("INSERT INTO products (category,sub_category,particle_size,volume_size,catalog_code,name,price,stock) VALUES (?,?,?,?,?,?,?,?)",
                  ("xbone","xbone","150-1000 µM",vol,code,f"X Bone | 150-1000µM | {vol}",0,50))
    # particle size 500-1000
    for code, vol in [("5016","0.3cc"),("5017","0.5cc"),("5018","1cc"),("5019","2cc"),("5020","5cc")]:
        c.execute("INSERT INTO products (category,sub_category,particle_size,volume_size,catalog_code,name,price,stock) VALUES (?,?,?,?,?,?,?,?)",
                  ("xbone","xbone","500-1000 µM",vol,code,f"X Bone | 500-1000µM | {vol}",0,50))
    # particle size 1000-2000
    for code, vol in [("6016","0.5cc"),("6017","1cc"),("6018","2cc"),("6019","5cc")]:
        c.execute("INSERT INTO products (category,sub_category,particle_size,volume_size,catalog_code,name,price,stock) VALUES (?,?,?,?,?,?,?,?)",
                  ("xbone","xbone","1000-2000 µM",vol,code,f"X Bone | 1000-2000µM | {vol}",0,50))
    # particle size 250-1000 MBA&DBM
    for code, vol in [("7016","0.3cc"),("7017","0.5cc"),("7018","1cc"),("7019","2cc"),("7020","5cc")]:
        c.execute("INSERT INTO products (category,sub_category,particle_size,volume_size,catalog_code,name,price,stock) VALUES (?,?,?,?,?,?,?,?)",
                  ("xbone","xbone","250-1000 µM (MBA&DBM)",vol,code,f"X Bone | 250-1000µM MBA&DBM | {vol}",0,50))

    # X Patch ممبران — ضخامت 0.3-0.5
    for code, size in [("1016","10×10"),("1017","15×10"),("1018","20×10"),("1019","20×15"),("1020","30×20"),("1021","40×20"),("1022","40×30")]:
        c.execute("INSERT INTO products (category,sub_category,particle_size,volume_size,catalog_code,name,price,stock) VALUES (?,?,?,?,?,?,?,?)",
                  ("xpatch","xpatch","0.3-0.5 mm",size,code,f"X Patch | 0.3-0.5mm | {size}cm",0,30))
    # X Patch — ضخامت 0.5-1
    for code, size in [("2016","10×10"),("2017","15×10"),("2018","20×10"),("2019","20×15"),("2020","30×20"),("2021","40×20"),("2022","40×30")]:
        c.execute("INSERT INTO products (category,sub_category,particle_size,volume_size,catalog_code,name,price,stock) VALUES (?,?,?,?,?,?,?,?)",
                  ("xpatch","xpatch","0.5-1 mm",size,code,f"X Patch | 0.5-1mm | {size}cm",0,30))
    # X Patch — ضخامت 1-1.5
    for code, size in [("3016","10×10"),("3017","15×10"),("3018","20×10"),("3019","20×15"),("3020","30×20"),("3021","40×20"),("3022","40×30")]:
        c.execute("INSERT INTO products (category,sub_category,particle_size,volume_size,catalog_code,name,price,stock) VALUES (?,?,?,?,?,?,?,?)",
                  ("xpatch","xpatch","1-1.5 mm",size,code,f"X Patch | 1-1.5mm | {size}cm",0,30))

    # Cross Linked X Patch — همان ضخامت‌ها
    for thick, base in [("0.3-0.5 mm","8"),("0.5-1 mm","9"),("1-1.5 mm","10")]:
        for i, size in enumerate(["10×10","15×10","20×10","20×15","30×20","40×20","40×30"]):
            code = f"{base}{1016+i}"
            c.execute("INSERT INTO products (category,sub_category,particle_size,volume_size,catalog_code,name,price,stock) VALUES (?,?,?,?,?,?,?,?)",
                      ("xpatch","crosslinked",thick,size,code,f"Cross Linked X Patch | {thick} | {size}cm",0,30))

# ── تنظیمات ──
def get_setting(key, default=""):
    conn = get_conn()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close(); return row["value"] if row else default

def set_setting(key, value):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (key, str(value)))
    conn.commit(); conn.close()

# ── کارکنان ──
def get_staff_roles(bale_id):
    conn = get_conn()
    rows = conn.execute("SELECT staff_role FROM staff_members WHERE bale_id=?", (bale_id,)).fetchall()
    conn.close(); return [r["staff_role"] for r in rows]

def add_staff_role(bale_id, staff_role, added_by=None):
    conn = get_conn()
    conn.execute("INSERT OR IGNORE INTO staff_members (bale_id,staff_role,added_by) VALUES (?,?,?)", (bale_id, staff_role, added_by))
    conn.commit(); conn.close()

def remove_staff_role(bale_id, staff_role):
    conn = get_conn()
    conn.execute("DELETE FROM staff_members WHERE bale_id=? AND staff_role=?", (bale_id, staff_role))
    conn.commit(); conn.close()

def remove_all_staff_roles(bale_id):
    conn = get_conn()
    conn.execute("DELETE FROM staff_members WHERE bale_id=?", (bale_id,))
    conn.commit(); conn.close()

def has_staff_role(bale_id, role): return role in get_staff_roles(bale_id)

def get_all_staff():
    conn = get_conn()
    rows = conn.execute("SELECT sm.*, u.full_name, u.phone FROM staff_members sm LEFT JOIN users u ON sm.bale_id=u.bale_id ORDER BY sm.bale_id").fetchall()
    conn.close(); return rows

# ── کاربر ──
def get_user(bale_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE bale_id=?", (bale_id,)).fetchone()
    conn.close(); return row

def upsert_user(bale_id):
    conn = get_conn()
    conn.execute("INSERT OR IGNORE INTO users (bale_id) VALUES (?)", (bale_id,))
    conn.commit(); conn.close()

def update_user(bale_id, **kw):
    conn = get_conn()
    sets = ", ".join(f"{k}=?" for k in kw)
    conn.execute(f"UPDATE users SET {sets} WHERE bale_id=?", [*kw.values(), bale_id])
    conn.commit(); conn.close()

def get_all_users(limit=200):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM users ORDER BY joined_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close(); return rows

def ban_user(bale_id, val=1):
    conn = get_conn()
    conn.execute("UPDATE users SET is_banned=? WHERE bale_id=?", (val, bale_id))
    conn.commit(); conn.close()

# ── State ──
def get_state(bale_id):
    conn = get_conn()
    row = conn.execute("SELECT state,data FROM user_states WHERE bale_id=?", (bale_id,)).fetchone()
    conn.close()
    if row: return row["state"], json.loads(row["data"] or "{}")
    return None, {}

def set_state(bale_id, state, data=None):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO user_states (bale_id,state,data) VALUES (?,?,?)",
                 (bale_id, state, json.dumps(data or {}, ensure_ascii=False)))
    conn.commit(); conn.close()

def clear_state(bale_id):
    conn = get_conn()
    conn.execute("DELETE FROM user_states WHERE bale_id=?", (bale_id,))
    conn.commit(); conn.close()

# ── محصول ──
def get_products_by_category(category):
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT sub_category FROM products WHERE category=? AND is_active=1", (category,)).fetchall()
    conn.close(); return [r["sub_category"] for r in rows]

def get_particle_sizes(sub_category):
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT particle_size FROM products WHERE sub_category=? AND is_active=1 ORDER BY id", (sub_category,)).fetchall()
    conn.close(); return [r["particle_size"] for r in rows]

def get_volume_sizes(sub_category, particle_size):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM products WHERE sub_category=? AND particle_size=? AND is_active=1 ORDER BY id",
                        (sub_category, particle_size)).fetchall()
    conn.close(); return rows

def get_product(pid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    conn.close(); return row

def delete_product(pid):
    conn = get_conn()
    conn.execute("DELETE FROM products WHERE id=?", (pid,))
    conn.commit(); conn.close()

def get_all_products():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM products ORDER BY category,sub_category,particle_size,id").fetchall()
    conn.close(); return rows

def update_product(pid, **kw):
    conn = get_conn()
    sets = ", ".join(f"{k}=?" for k in kw)
    conn.execute(f"UPDATE products SET {sets} WHERE id=?", [*kw.values(), pid])
    conn.commit(); conn.close()

def add_product(category, sub_category, particle_size, volume_size, catalog_code, name, price, stock=0):
    conn = get_conn()
    conn.execute("INSERT INTO products (category,sub_category,particle_size,volume_size,catalog_code,name,price,stock) VALUES (?,?,?,?,?,?,?,?)",
                 (category, sub_category, particle_size, volume_size, catalog_code, name, price, stock))
    conn.commit(); conn.close()

def decrease_stock(pid, qty):
    conn = get_conn()
    conn.execute("UPDATE products SET stock=stock-? WHERE id=? AND stock>=?", (qty, pid, qty))
    conn.commit(); conn.close()

# ── سفارش ──
def create_order(bale_id, items, total, discount, final):
    conn = get_conn()
    num = "BX" + datetime.now().strftime("%y%m%d%H%M%S")
    conn.execute("INSERT INTO orders (order_number,bale_id,items,total_amount,discount_amount,final_amount,status) VALUES (?,?,?,?,?,?,?)",
                 (num, bale_id, json.dumps(items, ensure_ascii=False), total, discount, final, "pending_payment"))
    conn.commit(); conn.close(); return num

def get_order(num):
    conn = get_conn()
    row = conn.execute("SELECT * FROM orders WHERE order_number=?", (num,)).fetchone()
    conn.close(); return row

def get_user_orders(bale_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM orders WHERE bale_id=? ORDER BY created_at DESC", (bale_id,)).fetchall()
    conn.close(); return rows

def update_order(num, **kw):
    kw["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_conn()
    sets = ", ".join(f"{k}=?" for k in kw)
    conn.execute(f"UPDATE orders SET {sets} WHERE order_number=?", [*kw.values(), num])
    conn.commit(); conn.close()

def get_orders_by_status(status):
    conn = get_conn()
    rows = conn.execute("SELECT o.*,u.full_name,u.phone,u.role,u.address FROM orders o JOIN users u ON o.bale_id=u.bale_id WHERE o.status=? ORDER BY o.created_at", (status,)).fetchall()
    conn.close(); return rows

def get_all_orders(limit=100):
    conn = get_conn()
    rows = conn.execute("SELECT o.*,u.full_name,u.phone FROM orders o JOIN users u ON o.bale_id=u.bale_id ORDER BY o.created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close(); return rows

# ── اخبار ──
def get_news(limit=10):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM news WHERE is_active=1 ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close(); return rows

def get_news_item(nid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM news WHERE id=?", (nid,)).fetchone()
    conn.close(); return row

def add_news(title, body):
    conn = get_conn()
    conn.execute("INSERT INTO news (title,body) VALUES (?,?)", (title, body))
    conn.commit(); conn.close()

def delete_news(nid):
    conn = get_conn()
    conn.execute("UPDATE news SET is_active=0 WHERE id=?", (nid,))
    conn.commit(); conn.close()

# ── روزنامه ──
def get_newspaper(limit=10):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM newspaper WHERE is_active=1 ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close(); return rows

def add_newspaper(title, file_id=None, url=None):
    conn = get_conn()
    conn.execute("INSERT INTO newspaper (title,file_id,url) VALUES (?,?,?)", (title, file_id, url))
    conn.commit(); conn.close()

def delete_newspaper(nid):
    conn = get_conn()
    conn.execute("UPDATE newspaper SET is_active=0 WHERE id=?", (nid,))
    conn.commit(); conn.close()

# ── کاتالوگ ──
def get_catalog_items(limit=20):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM catalog_items WHERE is_active=1 ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close(); return rows

def add_catalog_item(title, item_type, file_id=None, url=None, description=None):
    conn = get_conn()
    conn.execute("INSERT INTO catalog_items (title,item_type,file_id,url,description) VALUES (?,?,?,?,?)", (title, item_type, file_id, url, description))
    conn.commit(); conn.close()

def delete_catalog_item(cid):
    conn = get_conn()
    conn.execute("UPDATE catalog_items SET is_active=0 WHERE id=?", (cid,))
    conn.commit(); conn.close()

# ── سوالات متداول ──
def get_faqs():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM faq WHERE is_active=1 ORDER BY sort_order,id").fetchall()
    conn.close(); return rows

def get_faq(fid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM faq WHERE id=?", (fid,)).fetchone()
    conn.close(); return row

def add_faq(question, answer):
    conn = get_conn()
    conn.execute("INSERT INTO faq (question,answer) VALUES (?,?)", (question, answer))
    conn.commit(); conn.close()

def delete_faq(fid):
    conn = get_conn()
    conn.execute("UPDATE faq SET is_active=0 WHERE id=?", (fid,))
    conn.commit(); conn.close()

# ── تیکت ──
def create_ticket(bale_id, subject, text=None, file_id=None, file_type=None):
    import random
    code = f"BIO_{random.randint(10000,99999)}"
    conn = get_conn()
    conn.execute("INSERT INTO tickets (ticket_code,bale_id,subject,message_text,file_id,file_type) VALUES (?,?,?,?,?,?)",
                 (code, bale_id, subject, text, file_id, file_type))
    conn.commit(); conn.close(); return code

def get_ticket_by_code(code):
    conn = get_conn()
    row = conn.execute("SELECT * FROM tickets WHERE ticket_code=?", (code,)).fetchone()
    conn.close(); return row

def get_ticket_by_id(tid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM tickets WHERE id=?", (tid,)).fetchone()
    conn.close(); return row

def get_open_tickets():
    conn = get_conn()
    rows = conn.execute("SELECT t.*,u.full_name,u.phone FROM tickets t JOIN users u ON t.bale_id=u.bale_id WHERE t.status='open' ORDER BY t.created_at").fetchall()
    conn.close(); return rows

def get_all_tickets(limit=50):
    conn = get_conn()
    rows = conn.execute("SELECT t.*,u.full_name,u.phone FROM tickets t JOIN users u ON t.bale_id=u.bale_id ORDER BY t.created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close(); return rows

def update_ticket(code, **kw):
    conn = get_conn()
    sets = ", ".join(f"{k}=?" for k in kw)
    conn.execute(f"UPDATE tickets SET {sets} WHERE ticket_code=?", [*kw.values(), code])
    conn.commit(); conn.close()

# ── گزارش کارکنان ──
def add_staff_report(bale_id, rtype, text, file_id=None, file_type=None):
    conn = get_conn()
    conn.execute("INSERT INTO staff_reports (bale_id,report_type,report_text,file_id,file_type) VALUES (?,?,?,?,?)", (bale_id, rtype, text, file_id, file_type))
    conn.commit(); conn.close()

def get_staff_reports_by_user(bale_id, limit=30):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM staff_reports WHERE bale_id=? ORDER BY created_at DESC LIMIT ?", (bale_id, limit)).fetchall()
    conn.close(); return rows

def get_all_staff_reporters():
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT r.bale_id, u.full_name, COUNT(r.id) as report_count FROM staff_reports r JOIN users u ON r.bale_id=u.bale_id GROUP BY r.bale_id ORDER BY r.bale_id").fetchall()
    conn.close(); return rows

def get_report_detail(rid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM staff_reports WHERE id=?", (rid,)).fetchone()
    conn.close(); return row

# ── تخفیف ──
def get_discount(role):
    conn = get_conn()
    row = conn.execute("SELECT * FROM discounts WHERE role=?", (role,)).fetchone()
    conn.close(); return row

def get_all_discounts():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM discounts").fetchall()
    conn.close(); return rows

def set_discount(role, dtype, value):
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO discounts (role,discount_type,discount_value) VALUES (?,?,?)", (role, dtype, value))
    conn.commit(); conn.close()

def delete_discount(role):
    conn = get_conn()
    conn.execute("DELETE FROM discounts WHERE role=?", (role,))
    conn.commit(); conn.close()

def calc_discount(role, total):
    d = get_discount(role)
    if not d: return 0
    if d["discount_type"] == "percent": return int(total * d["discount_value"] / 100)
    return min(d["discount_value"], total)

# ── اقساط ────────────────────────────────────────────────
def create_installment(order_num, bale_id, total, paid, remaining, due_date):
    conn = get_conn()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS installments ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "order_number TEXT UNIQUE NOT NULL,"
        "bale_id INTEGER NOT NULL,"
        "total_amount INTEGER NOT NULL,"
        "paid_amount INTEGER DEFAULT 0,"
        "remaining_amount INTEGER NOT NULL,"
        "due_date TEXT NOT NULL,"
        "status TEXT DEFAULT 'pending',"
        "created_at TEXT DEFAULT CURRENT_TIMESTAMP)"
    )
    conn.execute(
        "INSERT OR IGNORE INTO installments (order_number,bale_id,total_amount,paid_amount,remaining_amount,due_date) VALUES (?,?,?,?,?,?)",
        (order_num, bale_id, total, paid, remaining, due_date)
    )
    conn.commit(); conn.close()

def get_installment(order_num):
    conn = get_conn()
    # اطمینان از وجود جدول
    conn.execute("CREATE TABLE IF NOT EXISTS installments (id INTEGER PRIMARY KEY AUTOINCREMENT, order_number TEXT UNIQUE NOT NULL, bale_id INTEGER NOT NULL, total_amount INTEGER NOT NULL, paid_amount INTEGER DEFAULT 0, remaining_amount INTEGER NOT NULL, due_date TEXT NOT NULL, status TEXT DEFAULT 'pending', created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    row = conn.execute("SELECT * FROM installments WHERE order_number=?", (order_num,)).fetchone()
    conn.close(); return row

def get_user_installments(bale_id):
    conn = get_conn()
    conn.execute("CREATE TABLE IF NOT EXISTS installments (id INTEGER PRIMARY KEY AUTOINCREMENT, order_number TEXT UNIQUE NOT NULL, bale_id INTEGER NOT NULL, total_amount INTEGER NOT NULL, paid_amount INTEGER DEFAULT 0, remaining_amount INTEGER NOT NULL, due_date TEXT NOT NULL, status TEXT DEFAULT 'pending', created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    rows = conn.execute("SELECT i.*, o.items FROM installments i LEFT JOIN orders o ON i.order_number=o.order_number WHERE i.bale_id=? AND i.status='pending' ORDER BY i.due_date", (bale_id,)).fetchall()
    conn.close(); return rows

def get_all_pending_installments():
    conn = get_conn()
    conn.execute("CREATE TABLE IF NOT EXISTS installments (id INTEGER PRIMARY KEY AUTOINCREMENT, order_number TEXT UNIQUE NOT NULL, bale_id INTEGER NOT NULL, total_amount INTEGER NOT NULL, paid_amount INTEGER DEFAULT 0, remaining_amount INTEGER NOT NULL, due_date TEXT NOT NULL, status TEXT DEFAULT 'pending', created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
    rows = conn.execute(
        "SELECT i.*, u.full_name, u.phone FROM installments i "
        "LEFT JOIN users u ON i.bale_id=u.bale_id WHERE i.status='pending' ORDER BY i.due_date"
    ).fetchall()
    conn.close(); return rows

def update_installment(order_num, paid_add):
    conn = get_conn()
    row = conn.execute("SELECT * FROM installments WHERE order_number=?", (order_num,)).fetchone()
    if not row: conn.close(); return
    new_paid = row["paid_amount"] + paid_add
    new_remaining = row["total_amount"] - new_paid
    status = "completed" if new_remaining <= 0 else "pending"
    conn.execute("UPDATE installments SET paid_amount=?, remaining_amount=?, status=? WHERE order_number=?",
                 (new_paid, max(0, new_remaining), status, order_num))
    conn.commit(); conn.close()

def has_pending_installment(bale_id):
    rows = get_user_installments(bale_id)
    return len(rows) > 0

# ── سفارشات تکمیل شده / در جریان ────────────────────────
def get_orders_completed():
    conn = get_conn()
    rows = conn.execute(
        "SELECT o.*,u.full_name,u.phone FROM orders o JOIN users u ON o.bale_id=u.bale_id "
        "WHERE o.status='shipped' ORDER BY o.updated_at DESC"
    ).fetchall()
    conn.close(); return rows

def get_orders_in_progress():
    conn = get_conn()
    rows = conn.execute(
        "SELECT o.*,u.full_name,u.phone FROM orders o JOIN users u ON o.bale_id=u.bale_id "
        "WHERE o.status IN ('approved','receipt_sent','pending_payment') ORDER BY o.created_at DESC"
    ).fetchall()
    conn.close(); return rows

def get_orders_by_period(days):
    from datetime import datetime, timedelta
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    conn = get_conn()
    rows = conn.execute(
        "SELECT o.*,u.full_name,u.phone,u.real_name,u.national_id,u.address,u.postal_code,u.medical_code "
        "FROM orders o JOIN users u ON o.bale_id=u.bale_id "
        "WHERE o.status='approved' AND o.created_at>=? ORDER BY o.created_at DESC", (since,)
    ).fetchall()
    conn.close(); return rows

def get_orders_last_week():
    return get_orders_by_period(7)

def get_customers_with_orders():
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT u.*, COUNT(o.id) as order_count, SUM(o.final_amount) as total_spent "
        "FROM users u JOIN orders o ON u.bale_id=o.bale_id "
        "WHERE o.status IN ('approved','shipped') "
        "GROUP BY u.bale_id ORDER BY u.full_name"
    ).fetchall()
    conn.close(); return rows

def add_installment_payment(order_num, bale_id, amount, file_id, ftype):
    conn = get_conn()
    conn.execute("INSERT INTO installment_payments (order_number,bale_id,amount,receipt_file_id,receipt_type) VALUES (?,?,?,?,?)",
                 (order_num, bale_id, amount, file_id, ftype))
    conn.commit(); conn.close()

def approve_installment_payment(payment_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM installment_payments WHERE id=?", (payment_id,)).fetchone()
    if not row: conn.close(); return
    conn.execute("UPDATE installment_payments SET status='approved' WHERE id=?", (payment_id,))
    conn.commit(); conn.close()
    update_installment(row["order_number"], row["amount"])

def get_all_installments():
    """همه اقساط فعال با اطلاعات کاربر"""
    conn = get_conn()
    rows = conn.execute(
        "SELECT i.*, u.full_name, u.phone FROM installments i "
        "LEFT JOIN users u ON i.bale_id=u.bale_id "
        "WHERE i.status='pending' ORDER BY i.due_date"
    ).fetchall()
    conn.close(); return rows

def get_pending_installment_payments():
    conn = get_conn()
    rows = conn.execute(
        "SELECT ip.*, u.full_name, u.phone FROM installment_payments ip "
        "LEFT JOIN users u ON ip.bale_id=u.bale_id WHERE ip.status='pending' ORDER BY ip.created_at"
    ).fetchall()
    conn.close(); return rows


# ── حضور و غیاب کارکنان ─────────────────────────────────
def clock_in(bale_id):
    """ثبت ورود"""
    from datetime import datetime
    conn = get_conn()
    now      = datetime.now()
    now_time = now.strftime("%H:%M:%S")   # HH:MM:SS
    now_date = now.strftime("%Y-%m-%d")   # YYYY-MM-DD
    # اگه همین امروز قبلاً ورود زده و هنوز خروج نداده
    row = conn.execute(
        "SELECT id FROM attendances WHERE bale_id=? AND date=? AND clock_out IS NULL",
        (bale_id, now_date)
    ).fetchone()
    if row:
        conn.close()
        return None  # قبلاً ورود ثبت شده
    conn.execute(
        "INSERT INTO attendances (bale_id,clock_in,date) VALUES (?,?,?)",
        (bale_id, now_time, now_date)
    )
    conn.commit(); conn.close()
    return now_time[:5]  # HH:MM

def clock_out(bale_id):
    """ثبت خروج"""
    from datetime import datetime
    conn = get_conn()
    now      = datetime.now()
    now_time = now.strftime("%H:%M:%S")
    now_date = now.strftime("%Y-%m-%d")
    # پیدا کردن آخرین ورود بدون خروج — هم امروز هم دیروز (شیفت شب)
    row = conn.execute(
        "SELECT id, clock_in, date FROM attendances "
        "WHERE bale_id=? AND clock_out IS NULL ORDER BY id DESC LIMIT 1",
        (bale_id,)
    ).fetchone()
    if not row:
        conn.close()
        return None
    fmt = "%H:%M:%S"
    t_in  = datetime.strptime(row["clock_in"], fmt)
    t_out = datetime.strptime(now_time, fmt)
    # اگه شیفت شب بود (خروج کمتر از ورود) یه روز اضافه کن
    diff_sec = (t_out - t_in).total_seconds()
    if diff_sec < 0:
        diff_sec += 86400
    minutes = max(0, int(diff_sec / 60))
    conn.execute(
        "UPDATE attendances SET clock_out=?, total_minutes=? WHERE id=?",
        (now_time, minutes, row["id"])
    )
    conn.commit(); conn.close()
    return now_time[:5], minutes

def get_today_attendance(bale_id):
    from datetime import datetime
    date = datetime.now().strftime("%Y-%m-%d")
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM attendances WHERE bale_id=? AND date=? ORDER BY id DESC LIMIT 1",
        (bale_id, date)
    ).fetchone()
    conn.close(); return row

def get_staff_attendance_reports(bale_id, limit=10):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM attendances WHERE bale_id=? ORDER BY created_at DESC LIMIT ?",
        (bale_id, limit)
    ).fetchall()
    conn.close(); return rows

def get_all_attendance_reporters():
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT a.bale_id, u.full_name, "
        "SUM(a.total_minutes) as total_minutes, COUNT(a.id) as session_count "
        "FROM attendances a JOIN users u ON a.bale_id=u.bale_id "
        "GROUP BY a.bale_id ORDER BY a.bale_id"
    ).fetchall()
    conn.close(); return rows

# ── اطلاعیه مخصوص کارکنان ───────────────────────────────
def get_staff_news(limit=10):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM staff_news WHERE is_active=1 ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close(); return rows

def add_staff_news(title, body):
    conn = get_conn()
    conn.execute("INSERT INTO staff_news (title,body) VALUES (?,?)", (title, body))
    conn.commit(); conn.close()

def delete_staff_news(nid):
    conn = get_conn()
    conn.execute("UPDATE staff_news SET is_active=0 WHERE id=?", (nid,))
    conn.commit(); conn.close()


# ── تسک‌های کارکنان ─────────────────────────────────────
def add_task(bale_id, title, body=None, file_id=None, file_type=None):
    conn = get_conn()
    conn.execute(
        "INSERT INTO tasks (bale_id,title,body,file_id,file_type) VALUES (?,?,?,?,?)",
        (bale_id, title, body, file_id, file_type)
    )
    conn.commit(); conn.close()

def get_user_tasks(bale_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE bale_id=? ORDER BY created_at DESC",
        (bale_id,)
    ).fetchall()
    conn.close(); return rows

def get_task(task_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    conn.close(); return row

def update_task_status(task_id, status):
    conn = get_conn()
    conn.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))
    conn.commit(); conn.close()

# ── چک و تعهدنامه ────────────────────────────────────────
def create_check_doc(order_num, bale_id, national_id, id_card_file):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO check_docs (order_number,bale_id,national_id,id_card_file) VALUES (?,?,?,?)",
        (order_num, bale_id, national_id, id_card_file)
    )
    conn.commit(); conn.close()

def update_check_doc(order_num, **kwargs):
    conn = get_conn()
    for k, v in kwargs.items():
        conn.execute(f"UPDATE check_docs SET {k}=? WHERE order_number=?", (v, order_num))
    conn.commit(); conn.close()

def get_check_doc(order_num):
    conn = get_conn()
    row = conn.execute("SELECT * FROM check_docs WHERE order_number=?", (order_num,)).fetchone()
    conn.close(); return row

def get_pending_check_docs():
    conn = get_conn()
    rows = conn.execute(
        "SELECT cd.*, u.full_name, u.phone, u.role, u.address, u.national_id as user_national_id "
        "FROM check_docs cd LEFT JOIN users u ON cd.bale_id=u.bale_id "
        "WHERE cd.status IN ('pending','need_check') ORDER BY cd.created_at"
    ).fetchall()
    conn.close(); return rows

def get_finance_staff():
    """لیست آیدی‌های مسئول مالی"""
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT bale_id FROM staff_members WHERE staff_role='finance'"
    ).fetchall()
    conn.close()
    return [r["bale_id"] for r in rows]

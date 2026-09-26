<div align="center">

# 🦷 BioX: Sales & Operations Bot for a Dental Products Company (Bale)

**A multi-role business bot on the [Bale](https://bale.ai) messenger** that runs a dental supply company's sales, orders, warehouse, staff reporting and customer support in one place.

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![Bale](https://img.shields.io/badge/Bale-python--bale--bot-00A884)
![SQLite](https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white)
![Excel](https://img.shields.io/badge/Excel-export-217346?logo=microsoftexcel&logoColor=white)

</div>

---

## ✨ Features

### 👤 Customer panel
- Registration with name, phone and **role** (dentist, clinic, student...). Each role can have its own discounts.
- Mandatory channel membership (configurable).
- **Ordering:** choose product, size and quantity, then enter full invoice or shipping details before payment.
- **Card-to-card payment** with receipt upload.
- Order history with status and **postal tracking code**.
- News and announcements, a **catalog** (PDF, links, videos) and a **ticket system** (text, image, voice).

### 🏭 Warehouse panel
- Orders ready to ship and **inventory management**.
- Entering a postal tracking code **automatically notifies the customer**.

### 👔 Staff panel
- **Daily reports** (text, image, file) and report history.

### 🔧 Admin panel
- Receipt approval and rejection.
- User management (block/unblock), products (price, stock, active, add new).
- **Role-based discounts** (percentage or fixed amount).
- Staff and role management, and reviewing staff reports.
- Ticket inbox with direct replies, announcements and broadcasts.
- Catalog management, full bot settings, and **Excel export** of data.

## 🧰 Tech Stack
Python · python-bale-bot · SQLite · openpyxl · jdatetime

## 🚀 Getting Started
```bash
pip install -r requirements.txt
cp .env.example .env    # BOT_TOKEN and SUPER_ADMIN_IDS
python bot.py
```
The database is created **empty on first run**.

## 📁 Project Structure
```
bot.py               # entry point and routing
database/db.py       # data layer
handlers/            # start, account, order, info, membership, staff, admin/panel
utils/               # keyboards, Jalali dates, Excel export
```

---
<div align="center">Built by <a href="https://github.com/mohagheghm511">@mohagheghm511</a></div>

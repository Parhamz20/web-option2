import sqlite3
import os


# -------------------------
# مسیر دیتابیس
# -------------------------

DB_PATH = os.path.join(
    os.getcwd(),
    "options.db"
)


# -------------------------
# اتصال به دیتابیس
# -------------------------

def get_connection():

    return sqlite3.connect(DB_PATH)


# -------------------------
# ساخت دیتابیس
# -------------------------

def create_database():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS calculations (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            tab_name TEXT,

            contract TEXT,

            stock REAL,

            strike REAL,

            final_price REAL,

            capital REAL,

            expiry_jalali TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # سازگاری با دیتابیس‌های قدیمی‌تر که ستون expiry_jalali را ندارند
    try:
        cursor.execute(
            "ALTER TABLE calculations ADD COLUMN expiry_jalali TEXT"
        )
    except sqlite3.OperationalError:
        # ستون از قبل وجود دارد
        pass

    connection.commit()
    connection.close()

    print("Database created successfully")


# -------------------------
# ذخیره اطلاعات
# -------------------------

def save_calculation(
    tab_name,
    contract,
    stock,
    strike,
    final_price,
    capital,
    expiry_jalali=""
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO calculations
        (
            tab_name,
            contract,
            stock,
            strike,
            final_price,
            capital,
            expiry_jalali
        )

        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        tab_name,
        contract,
        stock,
        strike,
        final_price,
        capital,
        expiry_jalali
    ))

    connection.commit()
    connection.close()

    print("اطلاعات ذخیره شد:", contract)


# -------------------------
# خواندن اطلاعات
# -------------------------

def get_calculations():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            tab_name,
            contract,
            stock,
            strike,
            final_price,
            capital,
            created_at,
            expiry_jalali

        FROM calculations

        ORDER BY id
    """)

    data = cursor.fetchall()

    connection.close()

    return data


# -------------------------
# حذف یک قرارداد
# -------------------------

def delete_calculation(tab_name, contract):

    print("DELETE FUNCTION RUNNING")
    print("GET CONNECTION:", get_connection)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM calculations
        WHERE TRIM(tab_name) = TRIM(?)
        AND TRIM(contract) = TRIM(?)
    """, (
        tab_name,
        contract
    ))

    deleted_rows = cursor.rowcount

    connection.commit()
    connection.close()

    print(
        "حذف از دیتابیس:",
        tab_name,
        "|",
        contract,
        "| تعداد:",
        deleted_rows
    )


# -------------------------
# حذف همه قراردادهای یک تب
# (برای پاک‌سازی قبل از دریافت اطلاعات تازه از بازار)
# -------------------------

def delete_tab_calculations(tab_name):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM calculations
        WHERE TRIM(tab_name) = TRIM(?)
    """, (
        tab_name,
    ))

    deleted_rows = cursor.rowcount

    connection.commit()
    connection.close()

    print(
        "پاک‌سازی قراردادهای قبلی تب:",
        tab_name,
        "| تعداد:",
        deleted_rows
    )


print("DATABASE FILE:", os.path.abspath(__file__))
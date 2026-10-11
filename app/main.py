"""
app/main.py

نسخه‌ی وب Backend برنامه‌ی Option Analyzer.

این فایل فقط لایه‌ی API رو می‌سازه؛ منطق واقعی (گرفتن داده از بازار،
فرمول اصلی محاسبات، دیتابیس) همون فایل‌های formulas.py، market_data.py
و database.py هستن که از نسخه‌ی دسکتاپ کپی شدن و دست‌نخورده می‌مونن.
لایه‌ی نمایشی (وضعیت ITM/OTM، کارمزد کارگزاری) در calculations.py قرار داره.

رفتار ذخیره‌سازی دقیقاً مثل نسخه‌ی دسکتاپه: هر بار /api/contracts با
موفقیت صدا زده بشه، نتیجه خودکار جایگزین داده‌ی قبلی همون نماد در
دیتابیس می‌شه. /api/tabs و /api/tabs/{tab_name} هم برای دیدن آخرین
نتیجه‌ی ذخیره‌شده هستن، بدون نیاز به درخواست تازه از بازار.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.market_data import (
    get_underlying_list,
    get_contracts_for_underlying,
    MarketDataError,
)
from app.calculations import compute_contract_result
from app.database import (
    create_database,
    save_calculation,
    get_calculations,
    delete_tab_calculations,
)

app = FastAPI(title="Option Analyzer API")

# اجازه‌ی دسترسی از فرانت‌اند (که ممکنه روی یک دامنه/پورت دیگر باشد).
# نکته‌ی امنیتی: وقتی دامنه‌ی نهایی فرانت‌اند مشخص شد، به‌جای "*"
# فقط همان آدرس دقیق را اینجا بگذارید.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """ساخت جدول دیتابیس (اگر از قبل وجود نداشته باشد)."""
    create_database()


@app.get("/health")
def health_check():
    """برای تست این‌که سرور بالا اومده و زنده‌ست."""
    return {"status": "ok"}


@app.get("/api/underlyings")
def api_underlyings():
    """لیست نمادهای پایه‌ای که آپشن فعال دارن."""
    try:
        underlyings = get_underlying_list()
    except MarketDataError as error:
        raise HTTPException(status_code=502, detail=str(error))

    return {"underlyings": underlyings}


@app.get("/api/contracts")
def api_contracts(
    underlying: str = Query(..., description="نام نماد پایه، مثلاً اهرم"),
    capital: float = Query(..., gt=0, description="آورده (سرمایه)"),
):
    """
    همه‌ی قراردادهای یک نماد پایه را زنده از بازار می‌گیرد، محاسبه
    می‌کند، و نتیجه را جایگزین داده‌ی قبلی همین نماد در دیتابیس می‌کند.
    """

    underlying = underlying.strip()

    if not underlying:
        raise HTTPException(status_code=400, detail="نام نماد نمی‌تواند خالی باشد.")

    try:
        result = get_contracts_for_underlying(underlying)
    except MarketDataError as error:
        raise HTTPException(status_code=502, detail=str(error))

    underlying_price = result["underlying_price"]
    raw_contracts = result["contracts"]

    if not raw_contracts:
        raise HTTPException(
            status_code=404, detail=f"هیچ قراردادی برای «{underlying}» یافت نشد."
        )

    # جایگزینی داده‌ی قدیمی این نماد با نتیجه‌ی تازه
    delete_tab_calculations(underlying)

    contracts = []

    for item in raw_contracts:
        save_calculation(
            underlying,
            item["symbol"],
            underlying_price,
            item["strike"],
            item["premium"],
            capital,
            item.get("expiry_jalali", ""),
        )

        contracts.append(
            compute_contract_result(
                item["symbol"],
                underlying_price,
                item["strike"],
                item["premium"],
                capital,
                item.get("expiry_jalali", ""),
            )
        )

    return {
        "underlying": underlying,
        "underlying_price": underlying_price,
        "capital": capital,
        "contracts": contracts,
    }


@app.get("/api/tabs")
def api_list_tabs():
    """
    لیست نمادهایی که قبلاً دریافت و ذخیره شده‌اند، به‌همراه تعداد
    قرارداد و آخرین زمان ذخیره. برای ساخت یک منوی «آخرین گزارش‌ها».
    """

    rows = get_calculations()

    tabs = {}

    for row in rows:
        tab_name = row[1]
        created_at = row[7]

        if tab_name not in tabs:
            tabs[tab_name] = {"tab_name": tab_name, "contract_count": 0, "updated_at": created_at}

        tabs[tab_name]["contract_count"] += 1
        tabs[tab_name]["updated_at"] = created_at

    return {"tabs": list(tabs.values())}


@app.get("/api/tabs/{tab_name}")
def api_get_tab(tab_name: str):
    """
    آخرین نتیجه‌ی ذخیره‌شده برای یک نماد را برمی‌گرداند، بدون درخواست
    تازه از بازار (دقیقاً همان داده‌ای که آخرین بار دریافت شده بود).
    """

    rows = get_calculations()
    matching_rows = [row for row in rows if row[1] == tab_name]

    if not matching_rows:
        raise HTTPException(
            status_code=404, detail=f"داده‌ای برای «{tab_name}» ذخیره نشده است."
        )

    underlying_price = matching_rows[-1][3]
    capital = matching_rows[-1][6]

    contracts = [
        compute_contract_result(
            row[2],              # contract
            row[3],               # stock (underlying_price)
            row[4],               # strike
            row[5],               # final_price (premium)
            row[6],               # capital
            row[8] if len(row) > 8 else "",  # expiry_jalali
        )
        for row in matching_rows
    ]

    return {
        "underlying": tab_name,
        "underlying_price": underlying_price,
        "capital": capital,
        "contracts": contracts,
    }


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


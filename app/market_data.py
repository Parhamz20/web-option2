"""
market_data.py

ماژول مستقل برای دریافت اطلاعات قراردادهای اختیار معامله از سایت TSETMC
با استفاده از کتابخانه‌ی algotik-tse.

این ماژول کاملاً جدا از main.py و database.py هست و فقط مسئولیتش
گرفتن داده از اینترنت و برگردوندن اون به‌صورت ساختاریافته‌ست.
هیچ‌کدوم از توابع این ماژول خودکار صدا زده نمی‌شن؛ فقط وقتی UI
(مثلاً با کلیک دکمه) صداشون بزنه اجرا می‌شن.
"""

import algotik_tse as att


class MarketDataError(Exception):
    """خطای مربوط به دریافت اطلاعات از بازار."""
    pass


def get_underlying_list(progress: bool = False) -> list[str]:
    """
    لیست نام تمام دارایی‌های پایه‌ای که در حال حاضر قرارداد اختیار
    معامله‌ی فعال دارن رو برمی‌گردونه.

    خروجی: لیستی از رشته‌ها، مثلاً ['اهرم', 'خودرو', 'فولاد', ...]
    """
    try:
        options_df = att.list_options(progress=progress)
    except Exception as exc:
        raise MarketDataError(
            f"خطا در دریافت لیست دارایی‌های پایه: {exc}"
        ) from exc

    if options_df is None or options_df.empty:
        return []

    underlyings = sorted(options_df["Underlying"].dropna().unique().tolist())
    return underlyings


def get_contracts_for_underlying(underlying: str, progress: bool = False) -> dict:
    """
    برای یک دارایی پایه‌ی مشخص، زنجیره‌ی کامل قراردادها (خرید و فروش)
    رو برمی‌گردونه.

    خروجی یک دیکشنری با این ساختار:
    {
        "underlying_price": 52510,
        "contracts": [
            {
                "symbol": "ضهرم5026",
                "option_type": "call",   # یا "put"
                "strike": 24000,
                "expiry_jalali": "1405/05/28",
            },
            ...
        ]
    }
    """
    if not underlying or not underlying.strip():
        raise MarketDataError("نام دارایی پایه نمی‌تواند خالی باشد.")

    try:
        chain = att.get_options_chain(underlying.strip(), progress=progress)
    except Exception as exc:
        raise MarketDataError(
            f"خطا در دریافت زنجیره‌ی اختیار معامله برای «{underlying}»: {exc}"
        ) from exc

    if chain is None:
        raise MarketDataError(f"داده‌ای برای «{underlying}» یافت نشد.")

    contracts = []

    for _, row in chain.get("calls", []).iterrows():
        contracts.append({
            "symbol": row["Symbol"],
            "option_type": "call",
            "strike": int(row["Strike"]),
            "premium": int(row["Close"]),
            "expiry_jalali": row.get("ExpiryJalali", ""),
        })

    for _, row in chain.get("puts", []).iterrows():
        contracts.append({
            "symbol": row["Symbol"],
            "option_type": "put",
            "strike": int(row["Strike"]),
            "premium": int(row["Close"]),
            "expiry_jalali": row.get("ExpiryJalali", ""),
        })

    return {
        "underlying_price": int(chain.get("underlying_price", 0)),
        "contracts": contracts,
    }


if __name__ == "__main__":
    # تست دستی ماژول از خط فرمان
    print("در حال دریافت لیست دارایی‌های پایه...")
    underlyings = get_underlying_list(progress=True)
    print(f"تعداد دارایی پایه: {len(underlyings)}")
    print(underlyings[:10])

    if underlyings:
        sample = underlyings[0]
        print(f"\nدر حال دریافت قراردادهای: {sample}")
        result = get_contracts_for_underlying(sample, progress=True)
        print("قیمت سهم پایه:", result["underlying_price"])
        print(f"تعداد قراردادها: {len(result['contracts'])}")
        for c in result["contracts"][:5]:
            print(c)

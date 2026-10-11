"""
app/calculations.py

منطق نمایشی که در نسخه‌ی دسکتاپ داخل main.py بود (نه formulas.py)،
اینجا به‌شکل یک ماژول مستقل بازسازی شده تا backend هم بتونه ازش
استفاده کنه. فرمول اصلی سود/آورده هنوز از formulas.py میاد و
دست‌نخورده می‌مونه؛ این فایل فقط لایه‌ی اضافه (وضعیت ITM/OTM،
کارمزد کارگزاری، تشخیص نوع قرارداد) رو فراهم می‌کنه.
"""

from app.formulas import calculate

# کارمزد کارگزاری که از سود کلی کسر می‌شود (همان مقدار نسخه‌ی دسکتاپ)
BROKERAGE_FEE_PERCENT = 1.5


def infer_option_type(symbol):
    """
    نوع قرارداد (خرید/فروش) را از روی حرف اول نماد تشخیص می‌دهد.
    در نمادهای اختیار معامله‌ی بورس ایران: «ض» = خرید، «ط» = فروش.
    """
    if not symbol:
        return None

    first_char = symbol[0]

    if first_char == "ض":
        return "call"

    if first_char == "ط":
        return "put"

    return None


def classify_moneyness(option_type, underlying_price, strike):
    """
    وضعیت قرارداد نسبت به قیمت فعلی سهم پایه را مشخص می‌کند:
    در سود (ITM) / در ضرر (OTM) / سربه‌سر (ATM)
    """
    if option_type == "call":
        if underlying_price > strike:
            return "در سود"
        if underlying_price < strike:
            return "در ضرر"
        return "سربه‌سر"

    if option_type == "put":
        if underlying_price < strike:
            return "در سود"
        if underlying_price > strike:
            return "در ضرر"
        return "سربه‌سر"

    return "-"


def compute_contract_result(symbol, underlying_price, strike, premium, capital, expiry_jalali=""):
    """
    یک قرارداد را با فرمول اصلی محاسبه می‌کند، سپس کارمزد کارگزاری را
    از سود کسر و آورده‌ی جدید را با همان سود تعدیل‌شده بازمحاسبه می‌کند
    (برخلاف نسخه‌ی دسکتاپ که فقط عدد سود را تغییر می‌داد، اینجا چون از
    صفر می‌سازیم، آورده هم با عدد درست هماهنگ می‌شود).

    خروجی یک دیکشنری ساده و آماده برای تبدیل به JSON است.
    """

    raw_result = calculate(symbol, underlying_price, strike, premium, capital)

    raw_profit = raw_result.get("سود کلی")
    option_type = infer_option_type(symbol)
    status = classify_moneyness(option_type, underlying_price, strike)

    is_loss = not isinstance(raw_profit, (int, float))
    profit_percent = None
    new_capital = None

    if not is_loss:
        adjusted_profit = raw_profit - BROKERAGE_FEE_PERCENT

        if adjusted_profit < 0:
            is_loss = True
        else:
            profit_percent = round(adjusted_profit, 2)
            new_capital = round(capital + (capital * adjusted_profit / 100), 2)

    return {
        "symbol": symbol,
        "option_type": option_type,
        "expiry_jalali": expiry_jalali,
        "underlying_price": underlying_price,
        "strike": strike,
        "status": status,
        "premium": premium,
        "capital": capital,
        "is_loss": is_loss,
        "profit_percent": profit_percent,
        "new_capital": new_capital,
    }

def calculate(contract_name, stock_price, strike_price, final_price, capital):

    
    # مرحله اول: محاسبه سود اولیه
    

    سود_اولیه = (final_price / stock_price) * 100


    
    # مرحله دوم: بررسی قیمت اعمال
    

    if strike_price < stock_price:

     اختلاف_کمتر = stock_price - strike_price
    
     اختلاف_کمتر_درصد = (اختلاف_کمتر / stock_price) * 100
    
     سود_کلی = سود_اولیه - اختلاف_کمتر_درصد


    elif strike_price > stock_price:
    
        اختلاف_بزرگتر = strike_price - stock_price
    
        اختلاف_بزرگتر_درصد = (اختلاف_بزرگتر / stock_price) * 100
    
        سود_کلی = سود_اولیه + اختلاف_بزرگتر_درصد


    else:

        # قیمت اعمال و قیمت نماد برابر هستند
        سود_کلی = سود_اولیه

# محاسبه آورده جدید
    درصد_آورده = (سود_کلی / 100) * capital

    capital = capital + درصد_آورده

    
    # نتیجه نهایی
    if سود_کلی < 0:
     سود_کلی = "خطا"

    else:
        سود_کلی = round(سود_کلی, 2)

    return {
        "نام قرارداد": contract_name,
        "قیمت اعمال": round(strike_price, 2),
        "قیمت نهایی": round(final_price, 2),
        "آورده": round(capital, 2),
        "سود کلی": سود_کلی
    }


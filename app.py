import streamlit as st
import yfinance as yf
import pandas as pd

# ==========================================
# 1. SET CONFIG & THEME (ตั้งค่าหน้าเว็บแบบกว้าง)
# ==========================================
st.set_page_config(
    page_title="DOOHUN - Stock Analytics Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. SAFE IMAGE DISPLAY (แก้บั๊ก MediaFileStorageError)
# ==========================================
def display_app_logo(image_filename="t-30-3.jpg", logo_width=65):
    """
    ฟังก์ชันแสดงโลโก้ ถ้าหาไฟล์ภาพบนเซิร์ฟเวอร์ไม่เจอ จะแสดงเป็น Text สวยๆ แทน แอปจะได้ไม่ล่ม
    """
    try:
        st.image(image_filename, width=logo_width)
    except Exception:
        # Fallback UI: ในกรณีที่ไฟล์ภาพหายหรือ Path ผิดพลาดบน GitHub Cloud
        st.markdown(
            """
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 25px;">
                <span style="font-size: 32px;">📈</span>
                <span style="font-size: 24px; font-weight: bold; color: #ffffff; font-family: sans-serif; letter-spacing: 1px;">DOOHUN</span>
            </div>
            """, 
            unsafe_allow_html=True
        )

# ==========================================
# 3. SAFE DATA FETCHING (แก้บั๊ก ราคาเป็น NaN)
# ==========================================
def get_clean_stock_data(ticker_symbol, period_selection="1y"):
    """
    ฟังก์ชันดึงข้อมูลหุ้นผ่าน yfinance พร้อมทำ Forward/Backward Fill เคลียร์ค่า NaN ทิ้งทันที
    """
    try:
        df = yf.download(ticker_symbol, period=period_selection)
        
        if df.empty:
            return None
            
        # เติมเต็มช่องว่างข้อมูลที่ยังไม่สมบูรณ์ (ป้องกันตลาดยังไม่ปิดหรือเปลี่ยนผ่านวันแล้วค่าเป็น NaN)
        df = df.ffill().bfill()
        return df
    except Exception as e:
        st.error(f"ไม่สามารถดึงข้อมูลของหุ้น {ticker_symbol} ได้ในขณะนี้: {e}")
        return None

# ==========================================
# 4. HTML STOCK CARD RENDER (แก้บั๊ก HTML หลุดเป็น String ดิบ)
# ==========================================
def render_custom_stock_card(ticker, full_name, price, change, change_percent, trend_status="ขาขึ้นแข็งแรง (BULLISH)"):
    """
    เรนเดอร์โครงสร้าง HTML CSS สวยๆ โดยใช้ st.markdown คู่กับ unsafe_allow_html=True
    """
    # คำนวณสีและสัญลักษณ์ตามสถานะบวกหรือลบ
    text_color = "#10b981" if change >= 0 else "#ef4444"
    arrow_icon = "▲" if change >= 0 else "▼"
    currency_unit = "THB" if ticker.endswith(".BK") else "USD"
    
    card_html = f"""
    <div style="background-color: #1c212d; border-radius: 8px; padding: 20px; border: 1px solid #2d3139; font-family: sans-serif; margin-bottom: 25px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
            <div>
                <span style="background-color: #3b82f6; color: white; padding: 3px 8px; border-radius: 5px; font-size: 11px; font-weight: 700;">STK</span>
                <h2 style="margin: 4px 0 2px 0; color: #ffffff; font-size: 32px; font-weight: 700;">
                    {ticker} <span style="font-size: 18px; color: #9ca3af; font-weight: 400;">{full_name}</span>
                </h2>
                <span style="background-color: rgba(16,185,129,0.15); color: #10b981; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold;">
                    ⚡ เทรนด์: {trend_status}
                </span>
            </div>
            
            <div style="text-align: right; min-width: 220px;">
                <div style="font-size: 36px; font-weight: 800; color: #ffffff;">
                    {price:,.2f} <span style="font-size: 16px; color: #9ca3af; font-weight: 400;">{currency_unit}</span>
                </div>
                <div style="font-size: 16px; font-weight: 700; color: {text_color};">
                    {arrow_icon} {abs(change):,.2f} ({change_percent:+.2f}%)
                </div>
                <div style="color: #9ca3af; font-size: 11px; margin-top: 4px;">
                    ดึงข้อมูลเรียลไทม์ผ่านระะบบ API เรียบร้อย
                </div>
            </div>
        </div>
    </div>
    """
    # ปล่อยให้ HTML ประมวลผลผ่านตัวเลือกนี้เพื่อความสวยงาม
    st.markdown(card_html, unsafe_allow_html=True)


# ==========================================
# 5. MAIN APPLICATION LOGIC
# ==========================================
def main():
    # เรียกใช้โลโก้ส่วนหัวแอปพลิเคชัน
    display_app_logo("t-30-3.jpg", logo_width=65)
    
    # ส่วนของ Sidebar ฝั่งซ้าย
    st.sidebar.header("📊 เมนูวิเคราะห์หุ้น")
    selected_stock = st.sidebar.selectbox(
        "เลือกหุ้นที่ต้องการตรวจสอบหน่วยลงทุน:",
        ["RKLB", "PTT.BK"]
    )
    
    # ดิกชันนารีเก็บชื่อเต็มของบริษัท
    stock_catalog = {
        "RKLB": "Rocket Lab Corporation",
        "PTT.BK": "PTT Public Company Limited"
    }
    
    # ทำการโหลดและเคลียร์ข้อมูลจาก API 
    df = get_clean_stock_data(selected_stock)
    
    if df is not None:
        try:
            # ป้องกันโครงสร้าง DataFrame ชั้นซ้อน (MultiIndex) ของ yfinance เวอร์ชันใหม่
            if isinstance(df['Close'], pd.DataFrame):
                close_series = df['Close'].iloc[:, 0]
            else:
                close_series = df['Close']
                
            # ดึงราคาปิดวันล่าสุด และวันก่อนหน้ามาเปรียบเทียบ
            latest_price = float(close_series.iloc[-1])
            previous_price = float(close_series.iloc[-2])
            
            # คำนวณส่วนต่างราคา
            price_change = latest_price - previous_price
            price_change_percent = (price_change / previous_price) * 100
            
            # เรนเดอร์กล่องข้อมูลแบบประกอบร่างเสร็จสมบูรณ์
            render_custom_stock_card(
                ticker=selected_stock,
                full_name=stock_catalog[selected_stock],
                price=latest_price,
                change=price_change,
                change_percent=price_change_percent
            )
            
            # แสดงกราฟราคาเสริมความโปร่งใสของข้อมูลด้านล่าง
            st.subheader(f"📈 ประวัติทิศทางราคาของ {selected_stock}")
            st.line_chart(close_series)
            
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดทางเทคนิคภายในโครงสร้าง DataFrame: {e}")
    else:
        st.warning("ระบบไม่สามารถเชื่อมต่อฐานข้อมูลตลาดหุ้นได้ กรุณาลองใหม่อีกครั้ง")

if __name__ == "__main__":
    main()

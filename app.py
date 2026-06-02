import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os

# 1. ตั้งค่าหน้าจอแบบกว้างพิเศษธีมมืด
st.set_page_config(page_title="DOOHUN Terminal vPro", layout="wide", initial_sidebar_state="collapsed")

# 2. คืนค่าระบบจำสถานะหุ้นเด่น (Session State)
if 'ticker_input' not in st.session_state:
    st.session_state.ticker_input = "RKLB"

# 3. จัดการโครงสร้าง CSS ธีมมืดสนิทแบบไร้ช่องว่างบรรทัด ป้องกันโค้ดหลุดหล่น
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Anuphan:wght@300;400;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background-color: #0d1117;
    color: #c9d1d9;
    font-family: 'Anuphan', 'Inter', sans-serif;
}

.brand-title {
    font-size: 28px;
    font-weight: 800;
    color: #ffffff;
    margin: 0;
}

.brand-tag {
    color: #58a6ff;
    font-size: 14px;
    font-weight: 400;
}

.dashboard-banner {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
}

.banner-layout {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 15px;
}

.crypto-card {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 15px;
}

.trend-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    margin-top: 8px;
}

.mini-data-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    margin-top: 10px;
    background: #0d1117;
    padding: 12px;
    border: 1px solid #30363d;
    border-radius: 8px;
}

.mini-label { color: #8b949e; font-size: 11px; font-weight: 600; }
.mini-value { color: #ffffff; font-size: 13px; font-weight: 700; }

.score-badge-circle {
    display: inline-block;
    width: 40px;
    height: 40px;
    line-height: 36px;
    text-align: center;
    border-radius: 50%;
    font-weight: 700;
    font-size: 14px;
    margin-right: 12px;
}

.target-bar-bg { background-color: #0d1117; height: 8px; border-radius: 4px; position: relative; margin: 20px 0 10px 0; border: 1px solid #30363d; }
.target-bar-fill { background: linear-gradient(90deg, #1f6feb, #238636); height: 6px; border-radius: 4px; }
.target-bar-pointer { position: absolute; top: -5px; width: 14px; height: 14px; background: #ffffff; border-radius: 50%; box-shadow: 0 0 6px #58a6ff; }

.stButton>button {
    border: 1px solid #30363d !important;
    background-color: #21262d !important;
    color: #c9d1d9 !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
}
.stButton>button:hover {
    border-color: #58a6ff !important;
    color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)

# 4. ข้อมูลสรุปบริษัทหุ้นไทย
thai_business_summaries = {
    "RKLB": "Rocket Lab เป็นผู้นำระดับโลกด้านการขนส่งอวกาศและระบบดาวเทียม ให้บริการยิงจรวดขนาดเล็ก (Electron) และกำลังพัฒนาจรวดขนาดใหญ่ (Neutron) รวมถึงผลิตโครงสร้างดาวเทียมประสิทธิภาพสูง",
    "JNJ": "Johnson & Johnson เป็นบริษัทเวชภัณฑ์และเทคโนโลยีทางการแพทย์ระดับโลก วิจัยและจัดจำหน่ายยาขนานเอกรวมถึงเครื่องมือแพทย์ที่ใช้เทคโนโลยีหุ่นยนต์สำหรับการผ่าตัดขั้นสูง",
    "XOM": "Exxon Mobil เป็นหนึ่งในบริษัทพลังงานและปิโตรเคมีข้ามชาติที่ใหญ่ที่สุดในโลก ดำเนินธุรกิจน้ำมันและก๊าซธรรมชาติครบวงจร ควบคู่กับการลงทุนในเทคโนโลยีพลังงานสะอาดและดักจับคาร์บอน",
    "ASTS": "AST SpaceMobile เป็นผู้บุกเบิกเครือข่ายบรอดแบนด์เซลลูลาร์ผ่านดาวเทียมวงโคจรต่ำ (LEO) ที่เชื่อมต่อสัญญาณอินเทอร์เน็ตความเร็วสูงเข้าสู่โทรศัพท์มือถือทั่วไปได้โดยตรง (Direct-to-Cell)",
    "AMZN": "Amazon เป็นผู้ให้บริการอีคอมเมิร์ซและระบบคลาวด์คอมพิวติ้งยักษ์ใหญ่ของโลก (AWS) รวมถึงเป็นผู้นำด้านการพัฒนาโมเดลปัญญาประดิษฐ์ (AI) และความบันเทิงดิจิทัลสตรีมมิ่ง",
    "MU": "Micron Technology เป็นผู้ผลิตชิ้นส่วนหน่วยความจำเซมิคอนดักเตอร์ชั้นนำ ผลิตชิ้นส่วน RAM (DRAM) และแฟลชไดรฟ์ (NAND) ซึ่งเป็นหัวใจหลักของศูนย์ประมวลผลข้อมูล AI"
}

# 5. คลังไอคอนและสีประจำแบรนด์ (ป้องกันระบบรูปภาพล่ม 100%)
stock_logo_icons = {"RKLB": "🚀", "JNJ": "🏥", "XOM": "🛢️", "ASTS": "📡", "AMZN": "📦", "MU": "💾"}
stock_logo_colors = {"RKLB": "#da3633", "JNJ": "#0e7490", "XOM": "#1f6feb", "ASTS": "#8957e5", "AMZN": "#f0883e", "MU": "#238636"}

# =========================================================================
# HEADER CONTROL (เซฟตี้ไฟล์รูปหน้าโปรไฟล์เจ้าของแอป)
# =========================================================================
col_logo, col_title = st.columns([1, 12])
with col_logo:
    try:
        if os.path.exists("t-30-3.jpg"):
            st.image("t-30-3.jpg", width=60)
        else:
            st.markdown("<h2 style='margin:0; text-align:center;'>📊</h2>", unsafe_allow_html=True)
    except:
        st.markdown("<h2 style='margin:0; text-align:center;'>📊</h2>", unsafe_allow_html=True)

with col_title:
    st.markdown("""
<div style="padding-top: 2px;">
    <h1 class="brand-title">DOOHUN <span class="brand-tag">| Intelligent Stock Terminal vPro</span></h1>
    <p style="margin: 0; color: #8b949e; font-size: 12px;">ระบบวิเคราะห์ข้อมูลเทคนิคอลและมูลค่าพื้นฐานแบบเรียลไทม์ (โหมดมืดสนิท)</p>
</div>
""", unsafe_allow_html=True)

st.write("---")

# =========================================================================
# QUICK WATCHLIST SHORTCUTS
# =========================================================================
st.markdown("<span style='color:#58a6ff; font-size:12px; font-weight:600; display:block; margin-bottom:6px;'>⭐ หุ้นโปรดเข้าดูด่วน (Quick Watchlist):</span>", unsafe_allow_html=True)
watchlist_tickers = ["RKLB", "JNJ", "XOM", "ASTS", "AMZN", "MU"]
w_cols = st.columns(len(watchlist_tickers) + 2)

for idx, sym in enumerate(watchlist_tickers):
    with w_cols[idx]:
        if st.button(f"▫️ {sym}", key=f"wl_{sym}", use_container_width=True):
            st.session_state.ticker_input = sym
            st.rerun()

# =========================================================================
# SEARCH AND DATA ENGINE
# =========================================================================
st.write("")
col_ctrl1, col_ctrl2 = st.columns([3, 1])
with col_ctrl1:
    ticker_input = st.text_input("🔍 พิมพ์ชื่อตัวย่อหุ้นสากลหรือหุ้นไทยที่ต้องการค้นหา (เช่น TSLA, AAPL, NVDA, PTT.BK):", key="ticker_input")
with col_ctrl2:
    time_frame = st.selectbox("📅 ช่วงเวลาประวัติราคากราฟ:", ["6 เดือน", "1 ปี", "2 ปี"], index=1)

period_map = {"6 เดือน": "6mo", "1 ปี": "1y", "2 ปี": "2y"}
ticker = ticker_input.upper().strip()

if ticker:
    try:
        stock_data = yf.Ticker(ticker)
        # ดึงประวัติราคาก่อนเพื่อความชัวร์ (ประวัติราคาแทบไม่มีวันล่ม)
        df = stock_data.history(period=period_map[time_frame])
        
        if df.empty:
            st.error(f"❌ ไม่พบข้อมูลสัญลักษณ์หุ้น '{ticker}' กรุณาตรวจสอบตัวย่อใหม่อีกครั้ง")
        else:
            # ดักความปลอดภัยในกรณีที่ระบบดึงข้อมูล .info ของ Yahoo ล่ม
            info = {}
            try:
                info = stock_data.info
                if not isinstance(info, dict):
                    info = {}
            except:
                info = {}

            # นำข้อมูลดิบจากกราฟมาสลับใช้เป็นค่าเริ่มต้น ป้องกันหน้าจอสีแดงล่มตัวแอป
            current_price = info.get('currentPrice') or info.get('regularMarketPrice') or df['Close'].iloc[-1]
            prev_close = info.get('previousClose') or (df['Close'].iloc[-2] if len(df) > 1 else current_price)
            price_change = current_price - prev_close
            price_change_pct = (price_change / prev_close) * 100
            currency = info.get('currency', 'USD')
            last_date_str = df.index[-1].strftime('%d/%m/%Y')

            recent_high = df['High'].tail(20).max()
            recent_low = df['Low'].tail(20).min()

            # คำนวณแนวโน้มจากเส้นเฉลี่ย MA50
            df['MA50'] = df['Close'].rolling(window=min(50, len(df))).mean()
            last_ma50 = df['MA50'].iloc[-1] if not df['MA50'].isna().all() else current_price
            
            if current_price > last_ma50 * 1.02:
                trend_text, trend_color, trend_bg = "ขาขึ้นชัดเจน (Bullish)", "#58a6ff", "rgba(88,166,255,0.1)"
            elif current_price < last_ma50 * 0.98:
                trend_text, trend_color, trend_bg = "ขาลงความเสี่ยงสูง (Bearish)", "#f85149", "rgba(248,81,73,0.1)"
            else:
                trend_text, trend_color, trend_bg = "แกว่งตัวในกรอบ (Sideways)", "#d29922", "rgba(210,153,34,0.1)"

            color_txt = "#238636" if price_change >= 0 else "#f85149"
            arrow = "▲" if price_change >= 0 else "▼"

            # วาดระบบโลโก้ความเสถียรสูง (ห้ามย่อหน้าบรรทัดเด็ดขาด)
            brand_color = stock_logo_colors.get(ticker, "#30363d")
            brand_icon = stock_logo_icons.get(ticker, ticker[0])
            
            logo_html = f'<div style="background-color: {brand_color}; width: 48px; height: 48px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: 700; color: #ffffff; border: 1px solid #30363d; float: left; margin-right: 12px;">{brand_icon}</div>'

            # =========================================================================
            # SECTION 1: TOP SUMMARY BANNER
            # =========================================================================
            st.markdown(f"""
<div class="dashboard-banner">
    <div class="banner-layout">
        <div>
            {logo_html}
            <div style="overflow: hidden;">
                <span style="background-color: #1f6feb; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 700;">{info.get('exchange', 'GLOBAL MARKET')}</span>
                <h2 style="margin: 2px 0 2px 0; color: #ffffff; font-size: 28px; font-weight:700;">{ticker} <span style="font-size:16px; color:#8b949e; font-weight:400;">{info.get('longName', '')}</span></h2>
                <span class="trend-badge" style="background-color: {trend_bg}; color: {trend_color}; border: 1px solid {trend_color};">⚡ เทรนด์: {trend_text}</span>
            </div>
        </div>
        <div style="text-align: right; min-width: 200px;">
            <div style="font-size: 32px; font-weight: 800; color: #ffffff; margin-bottom: 2px;">{current_price:,.2f} <span style="font-size: 14px; color: #8b949e; font-weight:400;">{currency}</span></div>
            <div style="font-size: 14px; font-weight: 700; color: {color_txt};">{arrow} {abs(price_change):,.2f} ({price_change_pct:+.2f}%)</div>
            <div style="color: #8b949e; font-size: 11px; margin-top: 2px;">ข้อมูล ณ วันที่: {last_date_str}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

            # =========================================================================
            # SECTION 2: METRICS & CHART GRID
            # =========================================================================
            col_chart, col_dcf, col_metrics = st.columns([5, 4, 3])

            # คอลัมน์กราฟหลัก
            with col_chart:
                st.markdown('<div class="crypto-card">', unsafe_allow_html=True)
                st.markdown("<h4 style='margin-top:0; color:#58a6ff; font-size:14px; font-weight:700;'>📊 ผลตอบแทนและทิศทางเทคนิคอล</h4>", unsafe_allow_html=True)
                
                df['EMA200'] = df['Close'].ewm(span=min(200, len(df)), adjust=False).mean()

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='ราคาปิด', line=dict(color='#58a6ff', width=2)))
                if not df['MA50'].isna().all():
                    fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], mode='lines', name='MA50', line=dict(color='#d29922', width=1.2)))
                if not df['EMA200'].isna().all():
                    fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], mode='lines', name='EMA200', line=dict(color='#238636', width=1.2)))

                fig.update_layout(
                    template='plotly_dark',
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    hovermode="x unified", height=300, margin=dict(l=10, r=10, t=10, b=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=10, color="#8b949e")),
                    yaxis=dict(gridcolor="#21262d", side="right", tickfont=dict(color="#8b949e")),
                    xaxis=dict(gridcolor="#21262d", tickfont=dict(color="#8b949e"))
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)

            # คอลัมน์คำนวณราคาเหมาะสม DCF
            with col_dcf:
                st.markdown('<div class="crypto-card">', unsafe_allow_html=True)
                st.markdown("<h4 style='margin-top:0; color:#db61a2; font-size:14px; font-weight:700;'>💎 โมเดลประเมินมูลค่าหุ้นส่วนลดกระแสเงินสด (DCF)</h4>", unsafe_allow_html=True)
                
                raw_fcf = info.get('freeCashflow') or 500000000
                raw_shares = info.get('sharesOutstanding') or 400000000
                
                input_fcf = st.number_input("กระแสเงินสดอิสระ (FCF):", value=float(raw_fcf), format="%.0f")
                input_shares = st.number_input("หุ้นจดทะเบียนทั้งหมด (Shares):", value=float(raw_shares), format="%.0f")
                
                growth_rate = st.slider("การเติบโตต่อเนื่อง 5 ปี (%):", 0.0, 40.0, 10.0, 0.5) / 100
                wacc_rate = st.slider("ต้นทุนความเสี่ยง WACC (%):", 5.0, 20.0, 9.0, 0.5) / 100

                if input_shares > 0 and wacc_rate > 0.02:
                    future_fcf = input_fcf * ((1 + growth_rate) ** 5)
                    terminal_value = (future_fcf * 1.02) / (wacc_rate - 0.02)
                    pv_terminal = terminal_value / ((1 + wacc_rate) ** 5)
                    intrinsic_value = (pv_terminal + info.get('totalCash', 0) - info.get('totalDebt', 0)) / input_shares
                    
                    if intrinsic_value <= 0: 
                        intrinsic_value = current_price * 0.88
                    
                    upside = ((intrinsic_value - current_price) / current_price) * 100
                    
                    st.markdown(f"""
<div style="background: #0d1117; padding: 12px; border-radius: 8px; border: 1px solid #30363d; margin-top:10px; text-align:center;">
    <span style="color:#8b949e; font-size:11px;">มูลค่าพื้นฐานที่คำนวณได้</span>
    <h3 style="margin:2px 0; color:#58a6ff; font-size:24px; font-weight:700;">{intrinsic_value:,.2f} {currency}</h3>
</div>
""", unsafe_allow_html=True)
                    
                    if intrinsic_value > current_price:
                        st.markdown(f"<p style='color:#238636; font-size:12px; font-weight:600; margin-top:5px;'>🟢 ราคาต่ำกว่าพื้นฐาน (Undervalued) คาดการณ์ช่องว่าง +{upside:.1f}%</p>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<p style='color:#f85149; font-size:12px; font-weight:600; margin-top:5px;'>🔴 ราคาสูงเกินพื้นฐานคำนวณ (Overvalued) {abs(upside):.1f}%</p>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # คอลัมน์กรอบราคาแนวรับ-แนวต้าน
            with col_metrics:
                st.markdown('<div class="crypto-card">', unsafe_allow_html=True)
                st.markdown("<h4 style='margin-top:0; color:#ffffff; font-size:13px; font-weight:700;'>🎯 กรอบราคาสมดุลจากโบรกเกอร์</h4>", unsafe_allow_html=True)
                
                t_mean = info.get('targetMeanPrice') or current_price * 1.10
                t_low = info.get('targetLowPrice') or current_price * 0.85
                t_high = info.get('targetHighPrice') or current_price * 1.35
                
                pct = ((current_price - t_low) / (t_high - t_low)) * 100 if (t_high - t_low) > 0 else 50
                pct = max(0, min(100, pct))
                
                st.markdown(f"""
<div style="font-size:12px; color:#8b949e;">เป้าหมายเฉลี่ยจากนักวิเคราะห์: <b style="color:#ffffff;">{t_mean:,.2f}</b></div>
<div class="target-bar-bg"><div class="target-bar-fill" style="width: {pct}%;"></div><div class="target-bar-pointer" style="left: {pct}%;"></div></div>
<div style="display: flex; justify-content: space-between; font-size: 10px; color: #8b949e; margin-bottom:5px;">
    <span>ต่ำสุด: {t_low:,.1f}</span> <span>สูงสุด: {t_high:,.1f}</span>
</div>

<div class="mini-data-grid">
    <div><span class="mini-label">แนวรับสำคัญ (20 วัน)</span><br><span class="mini-value" style="color:#238636;">{recent_low:,.2f}</span></div>
    <div><span class="mini-label">แนวต้านสำคัญ (20 วัน)</span><br><span class="mini-value" style="color:#f85149;">{recent_high:,.2f}</span></div>
</div>
""", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                # ดัชนีความแข็งแกร่งทางการเงิน
                st.markdown('<div class="crypto-card" style="padding: 12px 20px;">', unsafe_allow_html=True)
                roe = info.get('returnOnEquity', 0.08) * 100
                p_score = int(max(15, min(99, 50 + roe)))
                de_ratio = info.get('debtToEquity', 80)
                s_score = int(max(15, min(100, 125 - de_ratio)))

                st.markdown(f"""
<div style="display: flex; align-items: center; margin-bottom: 8px;">
    <div class="score-badge-circle" style="background: rgba(248,81,73,0.1); color: #f85149; border: 1px solid #f85149;">{p_score}</div>
    <div style="font-size:12px; color:#ffffff;"><b>คะแนนการทำกำไร</b><br><span style="color:#8b949e; font-size:11px;">Profitability Score</span></div>
</div>
<div style="display: flex; align-items: center;">
    <div class="score-badge-circle" style="background: rgba(35,134,54,0.1); color: #238636; border: 1px solid #238636;">{s_score}</div>
    <div style="font-size:12px; color:#ffffff;"><b>ความปลอดภัยด้านหนี้สิน</b><br><span style="color:#8b949e; font-size:11px;">Solvency Score</span></div>
</div>
""", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # =========================================================================
            # SECTION 3: BUSINESS INSIGHT
            # =========================================================================
            st.markdown('<div class="crypto-card">', unsafe_allow_html=True)
            st.markdown("<h4 style='margin-top:0; font-size:13px; color:#58a6ff; font-weight:700;'>ℹ️ ลักษณะโครงสร้างธุรกิจและช่องทางรายได้ (Business Summary)</h4>", unsafe_allow_html=True)
            
            if ticker in thai_business_summaries:
                business_desc = thai_business_summaries[ticker]
            else:
                business_desc = info.get('longBusinessSummary', 'ขออภัย ระบบไม่พบคำอธิบายลักษณะธุรกิจของบริษัทสัญลักษณ์นี้ในฐานข้อมูลปัจจุบัน')
                
            st.write(business_desc)
            st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"ระบบไม่สามารถเชื่อมต่อฐานข้อมูลราคา ณ ขณะนี้ได้ กรุณารีเฟรชหน้าจอใหม่อีกครั้ง (รายละเอียดความผิดพลาด: {e})")

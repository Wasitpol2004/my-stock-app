import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os
import re

# 1. ตั้งค่าหน้าจอแบบกว้างพิเศษเพื่อรองรับระบบ Dashboard หน้าเดียว
st.set_page_config(page_title="DOOHUN Terminal", layout="wide", initial_sidebar_state="collapsed")

# 2. ระบบจำสถานะหุ้นเด่น (Session State)
if 'ticker_input' not in st.session_state:
    st.session_state.ticker_input = "RKLB"

# 3. คลังสไตล์ธีมสีขาวและเส้นขอบคมชัด (Crisp Light Theme CSS)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Anuphan:wght@300;400;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #f8fafc;
        color: #0f172a;
        font-family: 'Anuphan', 'Inter', sans-serif;
    }
    
    /* หัวโลโก้แบรนด์ */
    .brand-title {
        font-size: 28px;
        font-weight: 800;
        color: #1e3a8a;
        margin: 0;
        line-height: 1.2;
    }
    .brand-tag {
        color: #64748b;
        font-size: 14px;
        font-weight: 400;
    }

    /* กล่องข้อมูลหลัก Top Banner (พื้นหลังขาว/ขอบเข้มชัดเจน) */
    .dashboard-banner {
        background-color: #ffffff;
        border: 2px solid #cbd5e1;
        border-radius: 14px;
        padding: 22px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .banner-layout {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 15px;
    }
    
    /* การ์ดจัดการที่มีกรอบชัดเจนสวยงาม */
    .crypto-card {
        background-color: #ffffff;
        border: 2px solid #cbd5e1;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.03);
    }
    
    /* สถานะเทรนด์ */
    .trend-badge {
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        margin-top: 8px;
    }
    
    /* ระบบตารางกรอบข้อมูลย่อย */
    .mini-data-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
        margin-top: 10px;
        background: #f1f5f9;
        padding: 12px;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
    }
    .mini-label { color: #475569; font-size: 11px; font-weight: 600; }
    .mini-value { color: #0f172a; font-size: 13px; font-weight: 700; }
    
    /* สไตล์วงกลมคะแนนดิบ */
    .score-badge-circle {
        display: inline-block;
        width: 44px;
        height: 44px;
        line-height: 42px;
        text-align: center;
        border-radius: 50%;
        font-weight: 700;
        font-size: 15px;
        margin-right: 12px;
    }
    
    /* หลอดแถบความปลอดภัยราคา */
    .target-bar-bg { background-color: #e2e8f0; height: 8px; border-radius: 4px; position: relative; margin: 20px 0 10px 0; border: 1px solid #cbd5e1; }
    .target-bar-fill { background: linear-gradient(90deg, #3b82f6, #10b981); height: 6px; border-radius: 4px; }
    .target-bar-pointer { position: absolute; top: -5px; width: 16px; height: 16px; background: #1e3a8a; border-radius: 50%; box-shadow: 0 0 6px rgba(0,0,0,0.2); }
    
    /* ปรับแต่งปุ่ม Watchlist ให้สวยงามเด่นชัด */
    .stButton>button {
        border: 2px solid #cbd5e1 !important;
        background-color: #ffffff !important;
        color: #0f172a !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        border-color: #2563eb !important;
        background-color: #eff6ff !important;
        color: #2563eb !important;
    }
    </style>
""", unsafe_allow_html=True)

# คลังข้อมูลคำอธิบายโมเดลธุรกิจภาษาไทยสำหรับหุ้นโปรดของคุณ
thai_business_summaries = {
    "RKLB": "Rocket Lab เป็นผู้นำระดับโลกด้านการขนส่งอวกาศและระบบดาวเทียม ดำเนินธุรกิจให้บริการยิงจรวดขนาดเล็ก (Electron) สำหรับส่งดาวเทียมสู่วงโคจร และกำลังพัฒนาจรวดขนาดใหญ่ (Neutron) นอกจากนี้ยังมีรายได้หลักจากการผลิตโครงสร้าง ระบบพลังงาน และชิ้นส่วนดาวเทียมประสิทธิภาพสูงให้แก่ภาครัฐและเอกชนทั่วโลก",
    "JNJ": "Johnson & Johnson เป็นบริษัทเวชภัณฑ์และเทคโนโลยีทางการแพทย์ที่ใหญ่ที่สุดแห่งหนึ่งของโลก ดำเนินธุรกิจวิจัย พัฒนา และจัดจำหน่ายยาขนานเอกในการรักษาโรคที่ซับซ้อน (เช่น โรคมะเร็ง และโรคภูมิคุ้มกัน) รวมถึงเครื่องมือแพทย์ที่ใช้นวัตกรรมขั้นสูงและเทคโนโลยีหุ่นยนต์สำหรับการผ่าตัดเพื่อยกระดับระบบสาธารณสุข",
    "XOM": "Exxon Mobil เป็นหนึ่งในบริษัทพลังงานและปิโตรเคมีข้ามชาติที่ใหญ่ที่สุดในโลก ดำเนินธุรกิจแบบครบวงจร ตั้งแต่การสำรวจ ขุดเจาะ และผลิตน้ำมันดิบรวมถึงก๊าซธรรมชาติ (Upstream) ไปจนถึงกระบวนการกลั่นน้ำมันเพื่อผลิตเป็นน้ำมันเชื้อเพลิงและเคมีภัณฑ์ (Downstream) ควบคู่กับการลงทุนในเทคโนโลยีการดักจับคาร์บอน",
    "ASTS": "AST SpaceMobile เป็นผู้บุกเบิกการสร้างเครือข่ายบรอดแบนด์เซลลูลาร์ผ่านดาวเทียมวงโคจรต่ำ (LEO) แห่งแรกของโลกที่สามารถเชื่อมต่อสัญญาณอินเทอร์เน็ตความเร็วสูงเข้าสู่โทรศัพท์มือถือสมาร์ทโฟนทั่วไปได้โดยตรง (Direct-to-Cell) โดยไม่จำเป็นต้องติดตั้งอุปกรณ์เสริมหรือเสารับสัญญาณพิเศษใดๆ เพื่อขจัดจุดอับสัญญาณทั่วโลก",
    "AMZN": "Amazon.com เป็นบริษัทยักษ์ใหญ่ด้านเทคโนโลยีและอีคอมเมิร์ซระดับโลก มีรายได้หลักจากแพลตฟอร์มค้าปลีกออนไลน์ ระบบสมาชิก Amazon Prime และธุรกิจคลาวด์คอมพิวติ้งระดับโลก (AWS - Amazon Web Services) รวมถึงการขยายโครงสร้างพื้นฐานไปสู่เทคโนโลยีปัญญาประดิษฐ์ (AI) และความบันเทิงดิจิทัลสตรีมมิ่ง",
    "MU": "Micron Technology เป็นผู้ผลิตนวัตกรรมเซมิคอนดักเตอร์และชิ้นส่วนหน่วยความจำชั้นนำของโลก ผลิตภัณฑ์หลักประกอบด้วยชิ้นส่วน RAM (DRAM) และหน่วยความจำแฟลช (NAND Flash) ซึ่งเป็นชิ้นส่วนฮาร์ดแวร์หัวใจสำคัญในอุตสาหกรรมคอมพิวเตอร์ ยานยนต์อัจฉริยะ โทรศัพท์มือถือ และระบบประมวลผลข้อมูลปัญญาประดิษฐ์ (AI Data Centers)"
}

# =========================================================================
# HEADER WITH MASCOT LOGO
# =========================================================================
col_logo, col_title = st.columns([1, 12])
with col_logo:
    if os.path.exists("t-30-3.jpg"):
        st.image("t-30-3.jpg", width=65)
    else:
        st.markdown("<h1 style='margin:0; text-align:center; padding-top:5px;'>📊</h1>", unsafe_allow_html=True)

with col_title:
    st.markdown("""
        <div style="padding-top: 5px;">
            <h1 class="brand-title">DOOHUN <span class="brand-tag">| Intelligent Stock Terminal vPro</span></h1>
            <p style="margin: 0; color: #475569; font-size: 13px; font-weight:600;">ระบบวิเคราะห์ข้อมูลหุ้นเรียลไทม์หน้าจอเดี่ยว (Light Mode)</p>
        </div>
    """, unsafe_allow_html=True)

st.write("---")

# =========================================================================
# QUICK WATCHLIST BAR (คลิกปุ๊บ สลับหุ้นปั๊บ สายสะดวกสบาย)
# =========================================================================
st.markdown("<span style='color:#1e3a8a; font-size:13px; font-weight:700; display:block; margin-bottom:8px;'>⭐ หุ้นโปรดของคุณ (Quick Watchlist):</span>", unsafe_allow_html=True)
watchlist_tickers = ["RKLB", "JNJ", "XOM", "ASTS", "AMZN", "MU"]
w_cols = st.columns(len(watchlist_tickers) + 2)

for idx, sym in enumerate(watchlist_tickers):
    with w_cols[idx]:
        if st.button(f"▫️ {sym}", key=f"wl_{sym}", use_container_width=True):
            st.session_state.ticker_input = sym
            st.rerun()

# =========================================================================
# CONTROL SEARCH BAR
# =========================================================================
st.write("")
col_ctrl1, col_ctrl2 = st.columns([3, 1])
with col_ctrl1:
    ticker_input = st.text_input("🔍 ค้นหาชื่อหุ้นอื่นเพิ่มเติม (พิมพ์ตัวย่อ เช่น AAPL, TSLA, PTT.BK):", key="ticker_input")
with col_ctrl2:
    time_frame = st.selectbox("📅 ช่วงเวลาของกราฟ:", ["6 เดือน", "1 ปี", "2 ปี"], index=1)

period_map = {"6 เดือน": "6mo", "1 ปี": "1y", "2 ปี": "2y"}
ticker = ticker_input.upper().strip()

if ticker:
    try:
        stock_data = yf.Ticker(ticker)
        df = stock_data.history(period=period_map[time_frame])
        
        if df.empty:
            st.error(f"❌ ไม่พบสัญลักษณ์หุ้นชื่อ '{ticker}' กรุณาตรวจสอบตัวย่อใหม่อีกครั้ง")
        else:
            try: info = stock_data.info
            except: info = {}

            # ข้อมูลตัวเลขสำคัญ
            current_price = info.get('currentPrice') or info.get('regularMarketPrice') or df['Close'].iloc[-1]
            prev_close = info.get('previousClose') or (df['Close'].iloc[-2] if len(df) > 1 else current_price)
            price_change = current_price - prev_close
            price_change_pct = (price_change / prev_close) * 100
            currency = info.get('currency', 'USD')
            last_date_str = df.index[-1].strftime('%d/%m/%Y')

            recent_high = df['High'].tail(20).max()
            recent_low = df['Low'].tail(20).min()

            # คำนวณทิศทางเทรนด์ด้วยค่าเฉลี่ย MA50
            df['MA50'] = df['Close'].rolling(window=min(50, len(df))).mean()
            last_ma50 = df['MA50'].iloc[-1] if not df['MA50'].isna().all() else current_price
            
            if current_price > last_ma50 * 1.03:
                trend_text, trend_color, trend_bg = "ขาขึ้นแข็งแกร่ง (Bullish)", "#10b981", "rgba(16,185,129,0.15)"
            elif current_price < last_ma50 * 0.97:
                trend_text, trend_color, trend_bg = "ขาลงความเสี่ยงสูง (Bearish)", "#ef4444", "rgba(239,68,68,0.15)"
            else:
                trend_text, trend_color, trend_bg = "ออกข้างเลือกข้าง (Sideways)", "#d97706", "rgba(217,119,6,0.15)"

            color_txt = "#10b981" if price_change >= 0 else "#ef4444"
            arrow = "▲" if price_change >= 0 else "▼"

            # ระบบดึงโลโก้บริษัทอัตโนมัติผ่านโดเมนเว็บไซต์ด้วย Clearbit API
            website_url = info.get('website', '')
            logo_html = ""
            if website_url:
                clean_domain = re.sub(r'(https?://)?(www\.)?', '', website_url).split('/')[0]
                logo_html = f'<img src="https://logo.clearbit.com/{clean_domain}" style="width:50px; height:50px; border-radius:8px; border:1px solid #cbd5e1; margin-right:15px; float:left;">'

            # =========================================================================
            # SECTION 1: TOP SUMMARY BANNER (ธีมสว่าง ขอบชัดเจน)
            # =========================================================================
            st.markdown(f"""
            <div class="dashboard-banner">
                <div class="banner-layout">
                    <div>
                        {logo_html}
                        <div style="overflow: hidden;">
                            <span style="background-color: #1e3a8a; color: white; padding: 3px 8px; border-radius: 5px; font-size: 11px; font-weight: 700;">{info.get('exchange', 'GLOBAL MARKET')}</span>
                            <h2 style="margin: 4px 0 2px 0; color: #0f172a; font-size: 32px; font-weight:700;">{ticker} <span style="font-size:18px; color:#475569; font-weight:400;">{info.get('longName', '')}</span></h2>
                            <span class="trend-badge" style="background-color: {trend_bg}; color: {trend_color}; border: 1px solid {trend_color};">⚡ เทรนด์: {trend_text}</span>
                        </div>
                    </div>
                    <div style="text-align: right; min-width: 220px;">
                        <div style="font-size: 36px; font-weight: 800; color: #0f172a; margin-bottom: 2px;">{current_price:,.2f} <span style="font-size: 16px; color: #64748b; font-weight:400;">{currency}</span></div>
                        <div style="font-size: 16px; font-weight: 700; color: {color_txt};">{arrow} {abs(price_change):,.2f} ({price_change_pct:+.2f}%)</div>
                        <div style="color: #64748b; font-size: 11px; margin-top: 4px;">อัปเดตล่าสุด: {last_date_str}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # =========================================================================
            # SECTION 2: GRID LAYOUT (มีเส้นขอบและกรอบข้อความสวยงาม)
            # =========================================================================
            col_chart, col_dcf, col_metrics = st.columns([5, 4, 3])

            # --- คอลัมน์ที่ 1: กราฟเทคนิคัลสไตล์สว่าง ---
            with col_chart:
                st.markdown('<div class="crypto-card">', unsafe_allow_html=True)
                st.markdown("<h4 style='margin-top:0; color:#1e3a8a; font-size:15px; font-weight:700;'>📈 กราฟราคาและเส้นเทรนด์เคลื่อนที่</h4>", unsafe_allow_html=True)
                
                df['EMA200'] = df['Close'].ewm(span=min(200, len(df)), adjust=False).mean()

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='ราคาปิด', line=dict(color='#2563eb', width=2.5)))
                if not df['MA50'].isna().all():
                    fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], mode='lines', name='MA50 (กลาง)', line=dict(color='#d97706', width=1.5)))
                if not df['EMA200'].isna().all():
                    fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], mode='lines', name='EMA200 (ยาว)', line=dict(color='#10b981', width=1.5)))

                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    hovermode="x unified", height=320, margin=dict(l=10, r=10, t=10, b=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=11, color="#475569")),
                    yaxis=dict(gridcolor="#e2e8f0", side="right", tickfont=dict(color="#475569")),
                    xaxis=dict(gridcolor="#e2e8f0", tickfont=dict(color="#475569"))
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)

            # --- คอลัมน์ที่ 2: ระบบคำนวณมูลค่า DCF มีกรอบชัดเจน ---
            with col_dcf:
                st.markdown('<div class="crypto-card">', unsafe_allow_html=True)
                st.markdown("<h4 style='margin-top:0; color:#6b21a8; font-size:15px; font-weight:700;'>💎 กรอบประเมินราคาเหมาะสม (DCF Valuation)</h4>", unsafe_allow_html=True)
                
                raw_fcf = info.get('freeCashflow') or 500000000
                raw_shares = info.get('sharesOutstanding') or 400000000
                
                input_fcf = st.number_input("กระแสเงินสดอิสระล่าสุด (FCF):", value=float(raw_fcf), format="%.0f")
                input_shares = st.number_input("จำนวนหุ้นจดทะเบียน (Shares):", value=float(raw_shares), format="%.0f")
                
                growth_rate = st.slider("คาดการณ์โต 5 ปีข้างหน้า (%):", 0.0, 40.0, 12.0, 0.5) / 100
                wacc_rate = st.slider("อัตราคิดลดความเสี่ยง WACC (%):", 5.0, 20.0, 8.5, 0.5) / 100

                if input_shares > 0 and wacc_rate > 0.02:
                    future_fcf = input_fcf * ((1 + growth_rate) ** 5)
                    terminal_value = (future_fcf * 1.02) / (wacc_rate - 0.02)
                    pv_terminal = terminal_value / ((1 + wacc_rate) ** 5)
                    intrinsic_value = (pv_terminal + info.get('totalCash', 0) - info.get('totalDebt', 0)) / input_shares
                    
                    if intrinsic_value <= 0: 
                        intrinsic_value = current_price * 0.85
                    
                    upside = ((intrinsic_value - current_price) / current_price) * 100
                    
                    st.markdown(f"""
                        <div style="background: #f8fafc; padding: 12px; border-radius: 10px; border: 2px solid #cbd5e1; margin-top:14px; text-align:center;">
                            <span style="color:#475569; font-size:12px; font-weight:600;">มูลค่าพื้นฐานที่แท้จริงตามทฤษฎี</span>
                            <h3 style="margin:4px 0 2px 0; color:#2563eb; font-size:26px; font-weight:700;">{intrinsic_value:,.2f} {currency}</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if intrinsic_value > current_price:
                        st.success(f"🟢 ต่ำกว่าพื้นฐาน (Undervalued) มีช่องว่างทำกำไร +{upside:.1f}%")
                    else:
                        st.warning(f"🔴 สูงกว่าพื้นฐาน (Overvalued) เกินมูลค่าที่แท้จริง {abs(upside):.1f}%")
                st.markdown('</div>', unsafe_allow_html=True)

            # --- คอลัมน์ที่ 3: เป้าหมายนักวิเคราะห์และคะแนนกรอบชัดเจน ---
            with col_metrics:
                st.markdown('<div class="crypto-card">', unsafe_allow_html=True)
                st.markdown("<h4 style='margin-top:0; color:#0f172a; font-size:14px; font-weight:700;'>🎯 กรอบราคาสมดุลจากโบรกเกอร์</h4>", unsafe_allow_html=True)
                
                t_mean = info.get('targetMeanPrice') or current_price * 1.15
                t_low = info.get('targetLowPrice') or current_price * 0.80
                t_high = info.get('targetHighPrice') or current_price * 1.40
                
                pct = ((current_price - t_low) / (t_high - t_low)) * 100 if (t_high - t_low) > 0 else 50
                pct = max(0, min(100, pct))
                
                st.markdown(f"""
                    <div style="font-size:12px; color:#475569;">ราคากลางเป้าหมายเฉลี่ย: <b style="color:#0f172a; font-size:13px;">{t_mean:,.2f}</b></div>
                    <div class="target-bar-bg"><div class="target-bar-fill" style="width: {pct}%;"></div><div class="target-bar-pointer" style="left: {pct}%;"></div></div>
                    <div style="display: flex; justify-content: space-between; font-size: 11px; color: #64748b; margin-bottom:5px;">
                        <span>ต่ำสุด: {t_low:,.1f}</span> <span>สูงสุด: {t_high:,.1f}</span>
                    </div>
                    
                    <div class="mini-data-grid">
                        <div><span class="mini-label">แนวรับสำคัญ (20 วัน)</span><br><span class="mini-value" style="color:#10b981;">{recent_low:,.2f}</span></div>
                        <div><span class="mini-label">แนวต้านสำคัญ (20 วัน)</span><br><span class="mini-value" style="color:#ef4444;">{recent_high:,.2f}</span></div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                # การ์ดสุขภาพการเงินกรอบคู่ชัดเจน
                st.markdown('<div class="crypto-card" style="padding: 14px 20px;">', unsafe_allow_html=True)
                roe = info.get('returnOnEquity', 0.09) * 100
                p_score = int(max(10, min(99, 50 + roe)))
                de_ratio = info.get('debtToEquity', 70)
                s_score = int(max(10, min(100, 130 - de_ratio)))

                st.markdown(f"""
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <div class="score-badge-circle" style="background: rgba(239,68,68,0.08); color: #ef4444; border: 2px solid #ef4444;">{p_score}</div>
                        <div style="font-size:12px; color:#0f172a;"><b>คะแนนการทำกำไร</b><br><span style="color:#64748b; font-size:11px;">Profitability Score</span></div>
                    </div>
                    <div style="display: flex; align-items: center;">
                        <div class="score-badge-circle" style="background: rgba(16,185,129,0.08); color: #10b981; border: 2px solid #10b981;">{s_score}</div>
                        <div style="font-size:12px; color:#0f172a;"><b>คะแนนความปลอดภัยหนี้</b><br><span style="color:#64748b; font-size:11px;">Solvency Score</span></div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # =========================================================================
            # SECTION 3: BOTTOM BUSINESS INSIGHT ภาษาไทยกรอบชัดเจน
            # =========================================================================
            st.markdown('<div class="crypto-card">', unsafe_allow_html=True)
            st.markdown("<h4 style='margin-top:0; font-size:14px; color:#1e3a8a; font-weight:700;'>ℹ️ ลักษณะการประกอบธุรกิจและโครงสร้างรายได้บริษัท (Business Insight)</h4>", unsafe_allow_html=True)
            
            # ดึงคำอธิบายภาษาไทยจากพจนานุกรมหลังบ้าน หากไม่มีจะแสดงภาษาอังกฤษแบบปลอดภัย
            if ticker in thai_business_summaries:
                business_desc = thai_business_summaries[ticker]
            else:
                raw_summary = info.get('longBusinessSummary', 'ขออภัย ไม่พบรายละเอียดโครงสร้างธุรกิจของสัญลักษณ์นี้ในระบบ')
                business_desc = f"⚠️ (หุ้นนอกรายการหลัก - แสดงผลต้นฉบับภาษาอังกฤษ) \n\n {raw_summary}"
                
            st.write(business_desc)
            st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูลหุ้น: {e}")

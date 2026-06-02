import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# 1. ตั้งค่าหน้าจอแบบกว้างพิเศษเพื่อรองรับระบบ Dashboard หน้าเดียว
st.set_page_config(page_title="DOOHUN Terminal", layout="wide", initial_sidebar_state="collapsed")

# 2. ระบบจำสถานะหุ้นเด่น (Session State) เพื่อรองรับปุ่มกดคลิกเดียวเปลี่ยนหุ้น
if 'ticker_input' not in st.session_state:
    st.session_state.ticker_input = "RKLB"

# 3. คลังสไตล์ความสวยงาม CSS (ปลอดภัย 100% ไม่รั่วไหล)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #08090b;
        color: #f1f5f9;
        font-family: 'Inter', sans-serif;
    }
    
    /* หัวโลโก้แบรนด์ */
    .brand-title {
        font-size: 26px;
        font-weight: 800;
        color: #ffffff;
        margin: 0;
        line-height: 1.2;
    }
    .brand-tag {
        color: #64748b;
        font-size: 13px;
        font-weight: 400;
    }

    /* กล่องข้อมูลหลัก Top Banner */
    .dashboard-banner {
        background: linear-gradient(135deg, #111318 0%, #0c0d10 100%);
        border: 1px solid #1e222b;
        border-radius: 16px;
        padding: 22px;
        margin-bottom: 20px;
    }
    .banner-layout {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 15px;
    }
    
    /* การ์ดจัดการ Grid หน้าเดียว */
    .crypto-card {
        background-color: #111318;
        border: 1px solid #1e222b;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* สถานะเทรนด์ */
    .trend-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    /* ระบบตาราง Grid ขนาดเล็กสำหรับช่องข้อมูลวันนี้ */
    .mini-data-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
        margin-top: 10px;
        background: #171a21;
        padding: 12px;
        border-radius: 10px;
    }
    .mini-label { color: #94a3b8; font-size: 11px; }
    .mini-value { color: #ffffff; font-size: 13px; font-weight: 600; }
    
    /* สไตล์วงกลมคะแนนดิบ */
    .score-badge-circle {
        display: inline-block;
        width: 44px;
        height: 44px;
        line-height: 44px;
        text-align: center;
        border-radius: 50%;
        font-weight: 700;
        font-size: 15px;
        margin-right: 12px;
    }
    
    /* หลอดแถบความปลอดภัยราคา */
    .target-bar-bg { background-color: #1e222b; height: 6px; border-radius: 3px; position: relative; margin: 20px 0 10px 0; }
    .target-bar-fill { background: linear-gradient(90deg, #3b82f6, #10b981); height: 6px; border-radius: 3px; }
    .target-bar-pointer { position: absolute; top: -5px; width: 16px; height: 16px; background: #ffffff; border-radius: 50%; box-shadow: 0 0 8px #3b82f6; }
    </style>
""", unsafe_allow_html=True)

# =========================================================================
# HEADER WITH LOGO IMAGE (ใช้ภาพ t-30-3.jpg เป็นโลโก้เว็บอย่างเป็นทางการ)
# =========================================================================
col_logo, col_title = st.columns([1, 12])
with col_logo:
    st.image("t-30-3.jpg", width=65)
with col_title:
    st.markdown("""
        <div style="padding-top: 5px;">
            <h1 class="brand-title">DOOHUN <span class="brand-tag">| Intelligent Stock Terminal vPro</span></h1>
            <p style="margin: 0; color: #475569; font-size: 12px;">ระบบวิเคราะห์ข้อมูลหุ้นเรียลไทม์หน้าจอเดี่ยว</p>
        </div>
    """, unsafe_allow_html=True)

st.write("---")

# =========================================================================
# FAST WATCHLIST BAR (แถบทางลัดสายสะดวกสบาย คลิกปุ๊บ ข้อมูลเปลี่ยนปั๊บ)
# =========================================================================
st.markdown("<span style='color:#64748b; font-size:12px; font-weight:600; display:block; margin-bottom:5px;'>⭐ หุ้นโปรดของคุณ (Quick Watchlist):</span>", unsafe_allow_html=True)
watchlist_tickers = ["RKLB", "JNJ", "XOM", "ASTS", "AMZN", "MU"]
w_cols = st.columns(len(watchlist_tickers) + 2) # เผื่อช่องว่างด้านท้าย

for idx, sym in enumerate(watchlist_tickers):
    with w_cols[idx]:
        if st.button(f"▪️ {sym}", key=f"wl_{sym}", use_container_width=True):
            st.session_state.ticker_input = sym
            st.rerun()

# =========================================================================
# CONTROL SEARCH BAR
# =========================================================================
st.write("")
col_ctrl1, col_ctrl2 = st.columns([3, 1])
with col_ctrl1:
    ticker_input = st.text_input("🔍 ค้นหาชื่อหุ้นอื่นเพิ่มเติม (เช่น AAPL, TSLA, PTT.BK, CPALL.BK):", key="ticker_input")
with col_ctrl2:
    time_frame = st.selectbox("📅 ช่วงเวลาของกราฟ:", ["6 เดือน", "1 ปี", "2 ปี"], index=1)

period_map = {"6 เดือน": "6mo", "1 ปี": "1y", "2 ปี": "2y"}
ticker = ticker_input.upper().strip()

if ticker:
    try:
        # โหลดข้อมูลดิบย้อนหลังผ่าน yfinance
        stock_data = yf.Ticker(ticker)
        df = stock_data.history(period=period_map[time_frame])
        
        if df.empty:
            st.error(f"❌ ไม่พบสัญลักษณ์หุ้นชื่อ '{ticker}' กรุณาตรวจสอบตัวย่อใหม่อีกครั้ง")
        else:
            try: info = stock_data.info
            except: info = {}

            # ฟังก์ชันคำนวณราคาและข้อมูลดิบ
            current_price = info.get('currentPrice') or info.get('regularMarketPrice') or df['Close'].iloc[-1]
            prev_close = info.get('previousClose') or (df['Close'].iloc[-2] if len(df) > 1 else current_price)
            price_change = current_price - prev_close
            price_change_pct = (price_change / prev_close) * 100
            
            open_price = info.get('open') or df['Open'].iloc[-1]
            high_price = info.get('dayHigh') or df['High'].iloc[-1]
            low_price = info.get('dayLow') or df['Low'].iloc[-1]
            volume = info.get('regularMarketVolume') or df['Volume'].iloc[-1]
            currency = info.get('currency', 'USD')
            last_date_str = df.index[-1].strftime('%d/%m/%Y')

            # คำนวณแนวรับ-แนวต้านอัตโนมัติ (High-Low Window 20 วันล่าสุด)
            recent_high = df['High'].tail(20).max()
            recent_low = df['Low'].tail(20).min()

            # ตรวจสอบทิศทางเทรนด์ด้วยค่าเฉลี่ยสัญญานเคลื่อนที่ MA50
            df['MA50'] = df['Close'].rolling(window=min(50, len(df))).mean()
            last_ma50 = df['MA50'].iloc[-1] if not df['MA50'].isna().all() else current_price
            
            if current_price > last_ma50 * 1.03:
                trend_text, trend_color, trend_bg = "ขาขึ้นแข็งแกร่ง (Bullish)", "#10b981", "rgba(16,185,129,0.1)"
            elif current_price < last_ma50 * 0.97:
                trend_text, trend_color, trend_bg = "ขาลงความเสี่ยงสูง (Bearish)", "#ef4444", "rgba(239,68,68,0.1)"
            else:
                trend_text, trend_color, trend_bg = "ออกข้างเลือกข้าง (Sideways)", "#eab308", "rgba(234,179,8,0.1)"

            color_txt = "#10b981" if price_change >= 0 else "#ef4444"
            arrow = "▲" if price_change >= 0 else "▼"

            # =========================================================================
            # SECTION 1: TOP SUMMARY BANNER
            # =========================================================================
            st.markdown(f"""
            <div class="dashboard-banner">
                <div class="banner-layout">
                    <div>
                        <span style="background-color: #2563eb; color: white; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700;">{info.get('exchange', 'GLOBAL MARKET')}</span>
                        <h2 style="margin: 6px 0 2px 0; color: #ffffff; font-size: 34px; font-weight:700;">{ticker} <span style="font-size:18px; color:#64748b; font-weight:400;">{info.get('longName', '')}</span></h2>
                        <span class="trend-badge" style="background-color: {trend_bg}; color: {trend_color}; border: 1px solid {trend_color};">⚡ เทรนด์ปัจจุบัน: {trend_text}</span>
                    </div>
                    <div style="text-align: right; min-width: 250px;">
                        <div style="font-size: 38px; font-weight: 800; color: #ffffff; margin-bottom: 2px;">{current_price:,.2f} <span style="font-size: 18px; color: #64748b; font-weight:400;">{currency}</span></div>
                        <div style="font-size: 16px; font-weight: 700; color: {color_txt};">{arrow} {abs(price_change):,.2f} ({price_change_pct:+.2f}%)</div>
                        <div style="color: #475569; font-size: 11px; margin-top: 4px;">ข้อมูลล่าสุด ณ วันที่: {last_date_str}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # =========================================================================
            # SECTION 2: ALL-IN-ONE GRID LAYOUT (3 คอลัมน์กว้าง 5:4:3)
            # =========================================================================
            col_chart, col_dcf, col_metrics = st.columns([5, 4, 3])

            # --- คอลัมน์ที่ 1: กราฟเทคนิคัลอัจฉริยะ ---
            with col_chart:
                st.markdown('<div class="crypto-card">', unsafe_allow_html=True)
                st.markdown("<h4 style='margin-top:0; color:#38bdf8; font-size:15px;'>📈 กราฟความเคลื่อนไหวและเส้นค่าเฉลี่ย</h4>", unsafe_allow_html=True)
                
                df['EMA200'] = df['Close'].ewm(span=min(200, len(df)), adjust=False).mean()

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='ราคาปิด (Close)', line=dict(color='#2563eb', width=2.5)))
                if not df['MA50'].isna().all():
                    fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], mode='lines', name='MA50 (กลาง)', line=dict(color='#eab308', width=1.2)))
                if not df['EMA200'].isna().all():
                    fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], mode='lines', name='EMA200 (ยาว)', line=dict(color='#10b981', width=1.2)))

                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    hovermode="x unified", height=320, margin=dict(l=10, r=10, t=10, b=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=11, color="#64748b")),
                    yaxis=dict(gridcolor="#1e222b", side="right", tickfont=dict(color="#64748b")),
                    xaxis=dict(gridcolor="#1e222b", tickfont=dict(color="#64748b"))
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)

            # --- คอลัมน์ที่ 2: ระบบคำนวณมูลค่าแท้จริง DCF ---
            with col_dcf:
                st.markdown('<div class="crypto-card">', unsafe_allow_html=True)
                st.markdown("<h4 style='margin-top:0; color:#c084fc; font-size:15px;'>💎 เครื่องประเมินราคาเหมาะสม (DCF Valuation)</h4>", unsafe_allow_html=True)
                
                raw_fcf = info.get('freeCashflow') or 500000000
                raw_shares = info.get('sharesOutstanding') or 400000000
                
                input_fcf = st.number_input("กระแสเงินสดอิสระ (Free Cash Flow):", value=float(raw_fcf), format="%.0f")
                input_shares = st.number_input("จำนวนหุ้นจดทะเบียนทั้งหมด (Shares):", value=float(raw_shares), format="%.0f")
                
                growth_rate = st.slider("การเติบโต 5 ปีข้างหน้า (Growth %):", 0.0, 40.0, 12.0, 0.5) / 100
                wacc_rate = st.slider("คิดลดความเสี่ยงบริษัท (WACC %):", 5.0, 20.0, 8.5, 0.5) / 100

                if input_shares > 0 and wacc_rate > 0.02:
                    future_fcf = input_fcf * ((1 + growth_rate) ** 5)
                    terminal_value = (future_fcf * 1.02) / (wacc_rate - 0.02)
                    pv_terminal = terminal_value / ((1 + wacc_rate) ** 5)
                    intrinsic_value = (pv_terminal + info.get('totalCash', 0) - info.get('totalDebt', 0)) / input_shares
                    
                    if intrinsic_value <= 0: 
                        intrinsic_value = current_price * 0.85
                    
                    upside = ((intrinsic_value - current_price) / current_price) * 100
                    
                    st.markdown(f"""
                        <div style="background: #131a26; padding: 12px; border-radius: 10px; border: 1px solid #1e293b; margin-top:14px; text-align:center;">
                            <span style="color:#94a3b8; font-size:12px;">มูลค่าที่แท้จริงตามทฤษฎีการเงิน</span>
                            <h3 style="margin:4px 0 2px 0; color:#38bdf8; font-size:26px;">{intrinsic_value:,.2f} {currency}</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if intrinsic_value > current_price:
                        st.success(f"🟢 ถูกกว่าพื้นฐาน (Undervalued) มี Upside +{upside:.1f}%")
                    else:
                        st.warning(f"🔴 แพงกว่าพื้นฐาน (Overvalued) เกินราคาเป้าหมาย {abs(upside):.1f}%")
                st.markdown('</div>', unsafe_allow_html=True)

            # --- คอลัมน์ที่ 3: เป้าหมายนักวิเคราะห์ & สแกนสุขภาพการเงิน ---
            with col_metrics:
                st.markdown('<div class="crypto-card">', unsafe_allow_html=True)
                st.markdown("<h4 style='margin-top:0; color:#f1f5f9; font-size:14px;'>🎯 ความเห็นของโบรกเกอร์ (Wall St)</h4>", unsafe_allow_html=True)
                
                t_mean = info.get('targetMeanPrice') or current_price * 1.15
                t_low = info.get('targetLowPrice') or current_price * 0.80
                t_high = info.get('targetHighPrice') or current_price * 1.40
                
                pct = ((current_price - t_low) / (t_high - t_low)) * 100 if (t_high - t_low) > 0 else 50
                pct = max(0, min(100, pct))
                
                st.markdown(f"""
                    <div style="font-size:11px; color:#94a3b8;">เป้าหมายราคากลางเฉลี่ย: <b style="color:#ffffff; font-size:13px;">{t_mean:,.2f}</b></div>
                    <div class="target-bar-bg"><div class="target-bar-fill" style="width: {pct}%;"></div><div class="target-bar-pointer" style="left: {pct}%;"></div></div>
                    <div style="display: flex; justify-content: space-between; font-size: 10px; color: #475569; margin-bottom:5px;">
                        <span>ต่ำสุด: {t_low:,.1f}</span> <span>สูงสุด: {t_high:,.1f}</span>
                    </div>
                    
                    <div class="mini-data-grid">
                        <div><span class="mini-label">กรอบแนวรับ (20 วัน)</span><br><span class="mini-value" style="color:#10b981;">{recent_low:,.2f}</span></div>
                        <div><span class="mini-label">กรอบแนวต้าน (20 วัน)</span><br><span class="mini-value" style="color:#ef4444;">{recent_high:,.2f}</span></div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                # การ์ดคะแนนพื้นฐาน
                st.markdown('<div class="crypto-card" style="padding: 14px 20px;">', unsafe_allow_html=True)
                roe = info.get('returnOnEquity', 0.09) * 100
                p_score = int(max(10, min(99, 50 + roe)))
                de_ratio = info.get('debtToEquity', 70)
                s_score = int(max(10, min(100, 130 - de_ratio)))

                st.markdown(f"""
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <div class="score-badge-circle" style="background: rgba(239,68,68,0.1); color: #ef4444; border: 1px solid #ef4444;">{p_score}</div>
                        <div style="font-size:12px;"><b>คะแนนการทำกำไร</b><br><span style="color:#64748b; font-size:10px;">Profitability Score</span></div>
                    </div>
                    <div style="display: flex; align-items: center;">
                        <div class="score-badge-circle" style="background: rgba(16,185,129,0.1); color: #10b981; border: 1px solid #10b981;">{s_score}</div>
                        <div style="font-size:12px;"><b>คะแนนความปลอดภัยหนี้</b><br><span style="color:#64748b; font-size:10px;">Solvency Score</span></div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # =========================================================================
            # SECTION 3: BOTTOM BUSINESS INSIGHT
            # =========================================================================
            st.markdown('<div class="crypto-card">', unsafe_allow_html=True)
            st.markdown("<h4 style='margin-top:0; font-size:13px; color:#64748b; font-weight:600;'>ℹ️ ลักษณะการประกอบธุรกิจและรายได้บริษัท (Business Insight)</h4>", unsafe_allow_html=True)
            summary = info.get('longBusinessSummary', 'ขออภัย ระบบไม่พบข้อมูลรายละเอียดธุรกิจของสัญลักษณ์นี้')
            st.write(summary[:600] + "..." if len(summary) > 600 else summary)
            st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูลหุ้น: {e}")

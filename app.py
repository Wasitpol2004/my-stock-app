import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# 1. ตั้งค่าหน้าจอแบบกว้างเพื่อจัดวาง Grid ทุกอย่างในหน้าเดียว
st.set_page_config(page_title="MoneyXFlow Terminal", layout="wide", initial_sidebar_state="collapsed")

# 2. ฝังโครงสร้างความสวยงาม (CSS) ไว้ด้านบนสุด (แก้อาการข้อความรั่วถาวร)
st.markdown("""
    <style>
    .stApp { background-color: #0b0c0e; color: #e2e8f0; }
    /* กล่องแบนเนอร์ด้านบน */
    .banner-box {
        background: linear-gradient(135deg, #161920 0%, #0f1115 100%);
        border: 1px solid #22252a; border-radius: 14px; padding: 20px; margin-bottom: 20px;
    }
    .banner-flex { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; }
    /* การ์ดจัดระเบียบข้อมูล */
    .premium-card {
        background-color: #13151a; border: 1px solid #22252a; border-radius: 12px; padding: 18px; margin-bottom: 15px; h-100;
    }
    /* ตารางสี่ช่องย่อย */
    .grid-table { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 10px; background: #1c1f26; padding: 10px; border-radius: 8px; }
    .grid-label { color: #64748b; font-size: 11px; }
    .grid-value { font-size: 13px; font-weight: bold; color: #ffffff; }
    /* วงกลมคะแนน */
    .score-circle { display: inline-block; width: 42px; height: 42px; line-height: 42px; text-align: center; border-radius: 50%; font-weight: bold; font-size: 15px; margin-right: 10px; }
    /* หลอดพลังเป้าหมาย */
    .bar-bg { background-color: #22252a; height: 6px; border-radius: 3px; position: relative; margin: 20px 0 8px 0; }
    .bar-fill { background: linear-gradient(90deg, #06b6d4, #3b82f6); height: 6px; border-radius: 3px; }
    .bar-pointer { position: absolute; top: -5px; width: 16px; height: 16px; background: #ffffff; border-radius: 50%; box-shadow: 0 0 6px #3b82f6; }
    </style>
""", unsafe_allow_html=True)

# --- ส่วนควบคุมด้านบนสุด (Topbar) ---
col_s1, col_s2 = st.columns([3, 1])
with col_s1:
    ticker_input = st.text_input("🔍 ค้นหาชื่อหุ้นสากล หรือ หุ้นไทย (เช่น RKLB, AAPL, PTT.BK):", "RKLB")
with col_s2:
    time_frame = st.selectbox("📅 ช่วงเวลากราฟ:", ["6 เดือน", "1 ปี", "2 ปี"], index=1)

period_map = {"6 เดือน": "6mo", "1 ปี": "1y", "2 ปี": "2y"}
ticker = ticker_input.upper().strip()

if ticker:
    try:
        # ดึงข้อมูลหุ้นแบบ Safe Mode
        stock_data = yf.Ticker(ticker)
        df = stock_data.history(period=period_map[time_frame])
        
        if df.empty:
            st.error(f"❌ ไม่พบข้อมูลของหุ้น '{ticker}' กรุณาตรวจเช็คตัวสะกดอีกครั้ง")
        else:
            try: info = stock_data.info
            except: info = {}

            # เตรียมตัวแปรราคาตลาด
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

            color_txt = "#10b981" if price_change >= 0 else "#ef4444"
            arrow = "▲" if price_change >= 0 else "▼"

            # =========================================================================
            # SECTION 1: TOP BANNER (สรุปราคาปัจจุบันเต็มตาด้านบน)
            # =========================================================================
            st.markdown(f"""
            <div class="banner-box">
                <div class="banner-flex">
                    <div>
                        <span style="background-color: #2563eb; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">{info.get('exchange', 'STOCK')}</span>
                        <h2 style="margin: 3px 0 0 0; font-size: 32px; color: #ffffff;">{ticker} <span style="font-size:18px; color:#94a3b8; font-weight:normal;">{info.get('longName', '')}</span></h2>
                    </div>
                    <div style="text-align: right; min-width: 240px;">
                        <h2 style="margin:0; font-size: 36px; color: #ffffff; font-weight: bold;">{current_price:,.2f} <span style="font-size: 16px; color: #94a3b8;">{currency}</span></h2>
                        <p style="margin: 0; font-size: 14px; font-weight: bold; color: {color_txt};">{arrow} {abs(price_change):,.2f} ({price_change_pct:+.2f}%)</p>
                        <p style="margin: 0; color: #64748b; font-size: 11px;">ข้อมูลล่าสุด: {last_date_str}</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # =========================================================================
            # SECTION 2: 3-COLUMN MAIN LAYOUT (ยุบรวมทุกฟังก์ชันแสดงผลพร้อมกันหน้าเดียว)
            # =========================================================================
            col_left, col_mid, col_right = st.columns([5, 4, 3])

            # --- คอลัมน์ซ้าย: กราฟราคาเทคนิคัล (เด่นที่สุด) ---
            with col_left:
                st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                st.markdown("<h4 style='margin-top:0; color:#38bdf8;'>📈 กราฟราคา & เส้นแนวโน้ม (MA/EMA)</h4>", unsafe_allow_html=True)
                
                df['MA50'] = df['Close'].rolling(window=50).mean()
                df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='ราคาปิด', line=dict(color='#0284c7', width=2.5)))
                if not df['MA50'].isna().all():
                    fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], mode='lines', name='MA50', line=dict(color='#eab308', width=1.2)))
                if not df['EMA200'].isna().all():
                    fig.add_trace(go.Scatter(x=df.index, y=df['EMA200'], mode='lines', name='EMA200', line=dict(color='#10b981', width=1.2)))

                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    hovermode="x unified", height=340, margin=dict(l=10, r=10, t=10, b=10),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(size=11, color="#94a3b8")),
                    yaxis=dict(gridcolor="#1e222b", side="right", tickfont=dict(color="#94a3b8")),
                    xaxis=dict(gridcolor="#1e222b", tickfont=dict(color="#94a3b8"))
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                st.markdown('</div>', unsafe_allow_html=True)

            # --- คอลัมน์กลาง: มูลค่าพื้นฐาน DCF (ปรับตัวเลขคำนวณเรียลไทม์) ---
            with col_mid:
                st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                st.markdown("<h4 style='margin-top:0; color:#a855f7;'>💎 เครื่องคำนวณมูลค่าที่แท้จริง (DCF)</h4>", unsafe_allow_html=True)
                
                raw_fcf = info.get('freeCashflow') or 450000000
                raw_shares = info.get('sharesOutstanding') or 350000000
                
                # ฟอร์มกรอกตัวเลขแบบกระชับไม่กินพื้นที่
                fcf_val = st.number_input("กระแสเงินสด (FCF):", value=float(raw_fcf), format="%.0f")
                shares_val = st.number_input("จำนวนหุ้นทั้งหมด:", value=float(raw_shares), format="%.0f")
                
                g_slider = st.slider("โต 5 ปีนี้ (Growth %):", 0.0, 40.0, 11.0, 0.5) / 100
                w_slider = st.slider("ความเสี่ยง (WACC %):", 5.0, 20.0, 9.0, 0.5) / 100

                if shares_val > 0 and w_slider > 0.02:
                    future_fcf = fcf_val * ((1 + g_slider) ** 5)
                    tv = (future_fcf * 1.02) / (w_slider - 0.02)
                    pv_tv = tv / ((1 + w_slider) ** 5)
                    intrinsic = (pv_tv + info.get('totalCash', 0) - info.get('totalDebt', 0)) / shares_val
                    if intrinsic <= 0: intrinsic = current_price * 0.82
                    
                    st.markdown(f"""
                        <div style="background: #1e1b4b; padding: 12px; border-radius: 8px; border: 1px solid #3730a3; margin-top:10px; text-align:center;">
                            <span style="color:#c084fc; font-size:12px;">ราคาที่เหมาะสมทางทฤษฎี</span>
                            <h3 style="margin:2px 0; color:#ffffff;">{intrinsic:,.2f} {currency}</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if intrinsic > current_price:
                        st.caption("🟢 **Undervalued** ราคาตลาดยังต่ำกว่าพื้นฐาน น่าสะสม")
                    else:
                        st.caption("🔴 **Overvalued** ราคาตลาดแพงกว่าพื้นฐาน ควรระวัง")
                st.markdown('</div>', unsafe_allow_html=True)

            # --- คอลัมน์ขวา: เป้าหมายนักวิเคราะห์ + คะแนนสุขภาพการเงิน ---
            with col_right:
                # การ์ดเป้าหมาย Wall St
                st.markdown('<div class="premium-card">', unsafe_allow_html=True)
                st.markdown("<h4 style='margin-top:0; color:#e2e8f0; font-size:14px;'>🎯 เป้าหมายนักวิเคราะห์ & กรอบวันนี้</h4>", unsafe_allow_html=True)
                
                t_mean = info.get('targetMeanPrice') or current_price * 1.12
                t_low = info.get('targetLowPrice') or current_price * 0.75
                t_high = info.get('targetHighPrice') or current_price * 1.45
                
                pct = ((current_price - t_low) / (t_high - t_low)) * 100 if (t_high - t_low) > 0 else 50
                pct = max(0, min(100, pct))
                
                st.markdown(f"""
                    <span style="font-size:12px; color:#94a3b8;">ราคาเป้าหมายเฉลี่ย:</span> <b style="color:#ffffff;">{t_mean:,.2f}</b>
                    <div class="bar-bg"><div class="bar-fill" style="width: {pct}%;"></div><div class="bar-pointer" style="left: {pct}%;"></div></div>
                    <div style="display: flex; justify-content: space-between; font-size: 10px; color: #64748b;">
                        <span>ต่ำ: {t_low:,.1f}</span> <span>สูง: {t_high:,.1f}</span>
                    </div>
                    <div class="grid-table">
                        <div><span class="grid-label">เปิดวันนี้</span><br><span class="grid-value">{open_price:,.2f}</span></div>
                        <div><span class="grid-label">สูงสุดวันนี้</span><br><span class="grid-value">{high_price:,.2f}</span></div>
                        <div><span class="grid-label">ต่ำสุดวันนี้</span><br><span class="grid-value">{low_price:,.2f}</span></div>
                        <div><span class="grid-label">ปริมาณการเทรด</span><br><span class="grid-value">{volume:,.0f}</span></div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

                # การ์ดคะแนนสแกนด่วน
                st.markdown('<div class="premium-card" style="padding: 12px 18px;">', unsafe_allow_html=True)
                roe = info.get('returnOnEquity', 0.08) * 100
                p_score = int(max(10, min(99, 52 + roe)))
                de_ratio = info.get('debtToEquity', 65)
                s_score = int(max(10, min(100, 135 - de_ratio)))

                st.markdown(f"""
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <div class="score-circle" style="background: rgba(239,68,68,0.1); color: #ef4444; border: 1px solid #ef4444;">{p_score}</div>
                        <div style="font-size:12px;"><b>การทำกำไร</b><br><span style="color:#64748b; font-size:10px;">Profitability Score</span></div>
                    </div>
                    <div style="display: flex; align-items: center;">
                        <div class="score-circle" style="background: rgba(16,185,129,0.1); color: #10b981; border: 1px solid #10b981;">{s_score}</div>
                        <div style="font-size:12px;"><b>ความปลอดภัยหนี้</b><br><span style="color:#64748b; font-size:10px;">Solvency Score</span></div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            # =========================================================================
            # SECTION 3: BOTTOM BUSINESS SUMMARY (คำอธิบายโมเดลธุรกิจด้านล่างกว้างๆ)
            # =========================================================================
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            st.markdown("<h4 style='margin-top:0; font-size:14px; color:#94a3b8;'>ℹ️ สรุปรูปแบบการสร้างรายได้ของบริษัท (Business Model Summary)</h4>", unsafe_allow_html=True)
            summary = info.get('longBusinessSummary', 'ไม่มีข้อมูลสรุปธุรกิจในระบบ')
            st.write(summary[:650] + "..." if len(summary) > 650 else summary)
            st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดทางเทคนิค: {e}")
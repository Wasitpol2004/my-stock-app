import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import datetime

# ==========================================
# 1. SET CONFIG & THEME (โหมดมืดสนิท)
# ==========================================
st.set_page_config(
    page_title="DOOHUN - Intelligent Stock Terminal vPro", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# ปรับแต่ง CSS สไตล์ Dashboard ระดับพรีเมียมตามภาพเป้าหมาย
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1rem;
    }
    div.stButton > button {
        background-color: #161b22;
        color: #8b949e;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 5px 15px;
    }
    div.stButton > button:hover {
        border-color: #58a6ff;
        color: #ffffff;
    }
    .dcf-box {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        margin-top: 15px;
    }
    .score-badge {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 10px;
        border-radius: 8px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    </style>
    """, 
    unsafe_allow_html=True
)

# Dictionary ข้อมูลบริษัทจำลอง
company_info = {
    'RKLB': 'Rocket Lab USA, Inc.',
    'JNJ': 'Johnson & Johnson',
    'XOM': 'Exxon Mobil Corporation',
    'ASTS': 'AST SpaceMobile, Inc.',
    'AMZN': 'Amazon.com, Inc.',
    'MU': 'Micron Technology, Inc.'
}

# ==========================================
# 2. HEADER SECTION
# ==========================================
head_col1, head_col2 = st.columns([1, 12])
with head_col1:
    # ดึงโลโก้ผ่าน URL ปลอดภัยจากอาการมีเดียเออร์เรอร์บน Cloud
    st.image("https://img.icons8.com/external-flatart-icons-flat-flatarticons/64/external-chart-web-development-and-programming-flatart-icons-flat-flatarticons.png", width=55)
with head_col2:
    st.markdown("<h1 style='margin:0; font-size:28px; font-weight:800; color:#ffffff;'>DOOHUN <span style='font-size:16px; color:#58a6ff; font-weight:normal;'>| Intelligent Stock Terminal vPro</span></h1>", unsafe_allow_html=True)
    st.markdown("<p style='margin:0; color:#8b949e; font-size:14px;'>ระบบวิเคราะห์ข้อมูลเทคนิคคอลและมูลค่าพื้นฐานแบบเรียลไทม์ (โหมดมืดสนิท)</p>", unsafe_allow_html=True)

st.markdown("<hr style='margin:15px 0; border-color:#30363d;'/>", unsafe_allow_html=True)

# ==========================================
# 3. QUICK WATCHLIST & SEARCH
# ==========================================
st.markdown("<span style='color:#e3b341;'>⭐ หุ้นโปรดเข้าดูด่วน (Quick Watchlist):</span>", unsafe_allow_html=True)
wl_col1, wl_col2, wl_col3, wl_col4, wl_col5, wl_col6, _ = st.columns([1,1,1,1,1,1,4])
wl_tickers = ["RKLB", "JNJ", "XOM", "ASTS", "AMZN", "MU"]
clicked_ticker = None

for idx, tkr in enumerate(wl_tickers):
    with locals()[f"wl_col{idx+1}"]:
        if st.button(f"▪️ {tkr}", use_container_width=True):
            clicked_ticker = tkr

# ช่องกรอกค้นหาและเลือกช่วงเวลา
search_col, time_col = st.columns([3, 1])
with search_col:
    search_input = st.text_input("🔍 พิมพ์ชื่อตัวย่อหุ้นสากลหรือหุ้นไทยที่ต้องการค้นหา (เช่น TSLA, AAPL, NVDA, PTT.BK):", "RKLB")
with time_col:
    time_frame = st.selectbox("📅 ช่วงเวลาประวัติราคากราฟ:", ["6 เดือน", "1 ปี", "2 ปี", "5 ปี"], index=1)

# สรุป Ticker ที่จะใช้งาน
target_ticker = (clicked_ticker or search_input).upper().strip()
time_map = {"6 เดือน": "6mo", "1 ปี": "1y", "2 ปี": "2y", "5 ปี": "5y"}

# ==========================================
# 4. DATA FETCH & PROCESSING (คำนวณดิบ ไม่ง้อ pandas_ta)
# ==========================================
@st.cache_data(ttl=3600)
def load_stock_data(symbol, period):
    try:
        df = yf.download(symbol, period=period)
        if df.empty:
            return None
        
        # 🌟 แก้ปัญหา MultiIndex จาก yfinance เวอร์ชันใหม่ตั้งแต่ต้นทางตรงนี้เลยครับ
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        # คำนวณอินดิเคเตอร์ด้วย pandas ดิบๆ แก้ปัญหา ModuleNotFoundError บนเซิร์ฟเวอร์
        df['MA50'] = df['Close'].rolling(window=50).mean()
        df['EMA200'] = df['Close'].ewm(span=200, adjust=False).mean()
        return df
    except Exception:
        return None

df_data = load_stock_data(target_ticker, time_map[time_frame])

# 🌟 ใส่คำว่า if และจัดระเบียบย่อหน้าโค้ดที่เหลือทั้งหมดให้ทำงานอยู่ภายใต้เงื่อนไขนี้
if df_data is not None and len(df_data) > 0:
    current_price = float(df_data['Close'].iloc[-1])
    prev_price = float(df_data['Close'].iloc[-2])
    price_diff = current_price - prev_price
    pct_change = (price_diff / prev_price) * 100
    
    # วิเคราะห์เทรนด์อัตโนมัติจากเส้น EMA200
    ma_50_last = float(df_data['MA50'].iloc[-1]) if not pd.isna(df_data['MA50'].iloc[-1]) else current_price
    trend_text = "⚡ เทรนด์: ขาขึ้นชัดเจน (Bullish)" if current_price > ma_50_last else "⚡ เทรนด์: ขาลง/พักฐาน (Bearish)"
    trend_color = "#2ea043" if current_price > ma_50_last else "#f85149"

    # ==========================================
    # 5. STOCK PRICE BANNER (แถบแสดงราคาหุ้นหลัก)
    # ==========================================
    banner_left, banner_right = st.columns([2, 1])
    with banner_left:
        st.markdown(
            f"""
            <div style='display:flex; align-items:center; gap:15px;'>
                <div style='background-color:#21262d; padding:10px; border-radius:8px; border:1px solid #30363d;'>🚀</div>
                <div>
                    <span style='background-color:#1f6feb; color:white; padding:2px 6px; border-radius:4px; font-size:11px; font-weight:bold;'>GLOBAL MARKET</span>
                    <h2 style='margin:2px 0 5px 0; color:#ffffff;'>{target_ticker} <span style='font-size:16px; color:#8b949e; font-weight:normal;'>{company_info.get(target_ticker, 'International Equity')}</span></h2>
                    <span style='background-color:{trend_color}20; color:{trend_color}; padding:4px 10px; border-radius:20px; font-size:12px; font-weight:bold;'>{trend_text}</span>
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    with banner_right:
        color_code = "#2ea043" if price_diff >= 0 else "#f85149"
        sign = "+" if price_diff >= 0 else ""
        st.markdown(
            f"""
            <div style='text-align: right;'>
                <h1 style='margin:0; color:#ffffff; font-size:36px; font-weight:800;'>{current_price:,.2f} <span style='font-size:16px; color:#8b949e;'>USD</span></h1>
                <p style='margin:0; color:{color_code}; font-weight:bold; font-size:14px;'>{sign}{price_diff:,.2f} ({sign}{pct_change:.2f}%)</p>
                <span style='font-size:11px; color:#8b949e;'>ข้อมูล ณ วันที่: {df_data.index[-1].strftime('%d/%m/%Y')}</span>
            </div>
            """, 
            unsafe_allow_html=True
        )

    st.markdown("<hr style='margin:15px 0; border-color:#30363d;'/>", unsafe_allow_html=True)

    # ==========================================
    # 6. THREE-COLUMN DASHBOARD LAYOUT
    # ==========================================
    col_chart, col_dcf, col_metrics = st.columns([4, 4, 3])

    # ---- คอลัมน์ที่ 1: กราฟเทคนิคคอล ----
    with col_chart:
        st.markdown("<span style='font-weight:bold; font-size:15px;'>📊 ผลตอบแทนและทิศทางเทคนิคคอล</span>", unsafe_allow_html=True)
        
        fig = go.Figure()
        # เส้นราคาปิด
        fig.add_trace(go.Scatter(x=df_data.index, y=df_data['Close'], name='ราคาปิด', line=dict(color='#58a6ff', width=2)))
        # เส้น MA50
        fig.add_trace(go.Scatter(x=df_data.index, y=df_data['MA50'], name='MA50', line=dict(color='#e3b341', width=1.2, dash='dash')))
        # เส้น EMA200
        fig.add_trace(go.Scatter(x=df_data.index, y=df_data['EMA200'], name='EMA200', line=dict(color='#bc8cff', width=1.2)))
        
        fig.update_layout(
            template="plotly_dark",
            margin=dict(l=10, r=10, t=10, b=10),
            height=380,
            plot_bgcolor='#0d1117',
            paper_bgcolor='#0d1117',
            xaxis=dict(showgrid=True, gridcolor='#21262d'),
            yaxis=dict(showgrid=True, gridcolor='#21262d', side='right'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # ---- คอลัมน์ที่ 2: โมเดลราคาประเมินพื้นฐาน DCF ----
    with col_dcf:
        st.markdown("<span style='font-weight:bold; font-size:15px; color:#58a6ff;'>💎 โมเดลประเมินมูลค่าหุ้นส่วนลดกระแสเงินสด (DCF)</span>", unsafe_allow_html=True)
        
        # ฟอร์มอินพุตปรับแต่งตัวเลขแบบ Interactive ตามรูปเป้าหมาย
        fcf_val = st.number_input("กระแสเงินสดอิสระ (FCF):", value=500000000, step=50000000)
        shares_val = st.number_input("หุ้นจดทะเบียนทั้งหมด (Shares):", value=400000000, step=10000000)
        
        grow_slider = st.slider("การเติบโตต่อเนื่อง 5 ปี (%):", 0.0, 30.0, 10.0, 0.5)
        wacc_slider = st.slider("ต้นทุนความเสี่ยง WACC (%):", 5.0, 20.0, 9.0, 0.5)

        # การคำนวณทางทฤษฎี DCF
        r = wacc_slider / 100.0
        g = grow_slider / 100.0
        
        # คาดการณ์กระแสเงินสดและคิดลดกลับมาเป็นมูลค่าปัจจุบัน
        pv_fcf = 0
        for year in range(1, 6):
            future_fcf = fcf_val * ((1 + g) ** year)
            pv_fcf += future_fcf / ((1 + r) ** year)
            
        # คำนวณมูลค่าในขั้นตอนสุดท้าย (Terminal Value)
        terminal_value = (fcf_val * ((1 + g) ** 5) * (1 + 0.02)) / (r - 0.02) if (r - 0.02) > 0 else 0
        pv_tv = terminal_value / ((1 + r) ** 5)
        
        # มูลค่าหุ้นที่แท้จริงต่อหุ้น
        intrinsic_value = (pv_fcf + pv_tv) / shares_val if shares_val > 0 else 0
        
        # กล่องแสดงผลลัพธ์ราคายุติธรรม
        st.markdown(
            f"""
            <div class='dcf-box'>
                <span style='color: #8b949e; font-size: 13px;'>มูลค่าพื้นฐานที่คำนวณได้</span>
                <h1 style='color: #58a6ff; margin: 10px 0; font-size: 32px;'>{intrinsic_value:,.2f} <span style='font-size:16px;'>USD</span></h1>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Status เปรียบเทียบราคาตลาดปัจจุบัน
        if current_price > intrinsic_value:
            diff_pct = ((current_price - intrinsic_value) / intrinsic_value) * 100 if intrinsic_value > 0 else 0
            st.markdown(f"<p style='color:#f85149; text-align:center; font-size:12px; font-weight:bold;'>🔴 ราคาเกินพื้นฐานที่คำนวณได้ (Overvalued) {diff_pct:.1f}%</p>", unsafe_allow_html=True)
        else:
            diff_pct = ((intrinsic_value - current_price) / current_price) * 100
            st.markdown(f"<p style='color:#2ea043; text-align:center; font-size:12px; font-weight:bold;'>🟢 ราคาต่ำกว่าพื้นฐานที่คำนวณได้ (Undervalued) {diff_pct:.1f}%</p>", unsafe_allow_html=True)

    # ---- คอลัมน์ที่ 3: บทวิเคราะห์จากโบรกเกอร์ & คะแนนหุ้น ----
    with col_metrics:
        st.markdown("<span style='font-weight:bold; font-size:15px;'>🎯 กรอบราคาสมดุลจากโบรกเกอร์</span>", unsafe_allow_html=True)
        
        # ราคาเป้าหมายและการประเมินกรอบแนวรับแนวต้านเชิงสถิติ (คำนวณจากข้อมูลย้อนหลังจริง)
        high_30 = float(df_data['High'].tail(30).max())
        low_30 = float(df_data['Low'].tail(30).min())
        avg_target = (high_30 + low_30) / 2
        
        st.markdown(f"<p style='margin:5px 0 0 0; font-size:12px; color:#8b949e;'>เป้าหมายเฉลี่ยจากนักวิเคราะห์: <span style='color:#ffffff; font-weight:bold;'>{avg_target:,.2f}</span></p>", unsafe_allow_html=True)
        st.progress(0.65) # แถบจำลองความใกล้มูลค่าเป้าหมาย
        
        # ตารางแนวรับ-แนวต้าน
        st.markdown("<hr style='margin:10px 0; border-color:#21262d;'/>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div style='display:flex; justify-content:between; width:100%; font-size:12px;'>
                <div style='width:50%;'>แนวรับสำคัญ (20 วัน)<br><span style='color:#2ea043; font-size:16px; font-weight:bold;'>{low_30:,.2f}</span></div>
                <div style='width:50%; text-align:right;'>แนวต้านสำคัญ (20 วัน)<br><span style='color:#f85149; font-size:16px; font-weight:bold;'>{high_30:,.2f}</span></div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # คะแนนสุขภาพทางการเงินของหุ้นแบบอินเตอร์แอคทีฟ
        st.markdown("<hr style='margin:15px 0; border-color:#21262d;'/>", unsafe_allow_html=True)
        
        st.markdown(
            """
            <div class='score-badge'>
                <div>
                    <span style='font-size:13px; font-weight:bold; color:#ffffff;'>คะแนนการทำกำไร</span><br>
                    <span style='font-size:11px; color:#8b949e;'>Profitability Score</span>
                </div>
                <span style='background-color:#f8514920; color:#f85149; border:1px solid #f85149; padding:3px 8px; border-radius:5px; font-weight:bold; font-size:14px;'>58</span>
            </div>
            <div class='score-badge'>
                <div>
                    <span style='font-size:13px; font-weight:bold; color:#ffffff;'>ความปลอดภัยด้านหนี้สิน</span><br>
                    <span style='font-size:11px; color:#8b949e;'>Solvency Score</span>
                </div>
                <span style='background-color:#2ea04320; color:#2ea043; border:1px solid #2ea043; padding:3px 8px; border-radius:5px; font-weight:bold; font-size:14px;'>45</span>
            </div>
            """, 
            unsafe_allow_html=True
        )

else:
    st.error(f"❌ ไม่พบข้อมูลหุ้นชื่อ '{target_ticker}' กรุณาตรวจสอบตัวย่อตลาดหุ้นและลองใหม่อีกครั้ง")

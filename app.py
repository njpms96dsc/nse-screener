import streamlit as st
import io, csv, requests
from groq import Groq

st.set_page_config(page_title="Hedge Fund Screener", layout="wide")
st.title("📊 AI-Powered Institutional Fundamental Screener")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("🔑 Credentials & Settings")
groq_api_key = st.sidebar.text_input("Groq API Key", type="password")
selected_model = st.sidebar.selectbox("LLM Brain", ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"])

# --- STEP 1: PORTFOLIO INTAKE ---
st.subheader("📁 Step 1: Provide Your Tickers")
input_method = st.radio("Input method:", ["Upload CSV File", "Paste Symbols Text Box"])
raw_symbols = []

if input_method == "Upload CSV File":
    uploaded_file = st.file_uploader("Upload stock list file:", type=None)
    if uploaded_file is not None:
        try:
            text_data = uploaded_file.getvalue().decode("utf-8", errors="ignore")
            reader = csv.reader(io.StringIO(text_data))
            for row in reader:
                if row and len(row) >= 3:
                    sym = str(row[2]).strip().replace('"', '').upper()
                    if sym and sym not in ['SYMBOL', 'TICKER', 'NAME', '']: raw_symbols.append(sym)
            raw_symbols = list(set(raw_symbols))
            if raw_symbols: st.success(f"Parsed! Extracted **{len(raw_symbols)}** symbols from column 3.")
        except Exception as e: st.error(f"File reading issue: {str(e)}")
else:
    text_input = st.text_area("Paste symbols (split by space/comma):", value="SBIN, RELIANCE, INFY")
    if text_input: raw_symbols = list(set([s.strip().upper() for s in text_input.replace(",", " ").split() if s.strip()]))

if raw_symbols:
    formatted_tickers = [s if s.endswith('.NS') else f"{s}.NS" for s in raw_symbols if s]
    st.write(f"Total Unique Tickers Tracked: **{len(formatted_tickers)}**")
    
    st.subheader("🎯 Step 2: Select Targets for Synthesis")
    selected_tickers = st.multiselect("Choose targets to scan:", options=formatted_tickers, default=formatted_tickers[:min(3, len(formatted_tickers))])
    
    if not selected_tickers: st.warning("⚠️ Choose at least one target stock.")
    else:
        if st.button("Run Fundamental Intelligence Analysis 🚀"):
            combined_stock_data, progress_bar = "", st.progress(0)
            
            # FIREWALL BYPASS: Establish tracking session mimicking an active client layout
            hdrs = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}
            session = requests.Session()
            session.headers.update(hdrs)
            
            # Initial lookup to acquire native tracking headers from the server endpoint
            try: session.get("https://fc.yahoo.com", headers=hdrs, timeout=5)
            except Exception: pass
            
            import yfinance as yf
            
            with st.spinner("Harvesting High-Alpha Institutional Ratios..."):
                for idx, tkr in enumerate(selected_tickers):
                    try:
                        # Injecting the authorized session layer into the connection channel
                        stock = yf.Ticker(tkr, session=session)
                        info = stock.info
                        
                        name = info.get('longName') or info.get('shortName') or tkr
                        prc = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose') or 'N/A'
                        pe = info.get('trailingPE') or info.get('forwardPE') or 'N/A'
                        pb = info.get('priceToBook') or 'N/A'
                        roe = info.get('returnOnEquity') or 'N/A'
                        mgn = info.get('profitMargins') or 'N/A'
                        grw = info.get('revenueGrowth') or 'N/A'
                        fcf = info.get('freeCashflow') or 'N/A'
                        ins = info.get('heldPercentInsiders') or 'N/A'
                        
                        d2e = info.get('debtToEquity')
                        if d2e is None: d2e = "N/A (Banking Framework)" if "bank" in str(name).lower() else "N/A"
                        
                        if isinstance(mgn, float): mgn = f"{round(mgn*100,2)}%"
                        if isinstance(grw, float): grw = f"{round(grw*100,2)}%"
                        if isinstance(roe, float): roe = f"{round(roe*100,2)}%"
                        if isinstance(ins, float): ins = f"{round(ins*100,2)}%"
                        if isinstance(fcf, (int, float)): fcf = f"INR {fcf:,.2f}"
                        
                        combined_stock_data += f"== {name} ({tkr}) ==\nPrice: INR {prc} | PE: {pe} | P/B: {pb}\nROE: {roe} | Net Margin: {mgn} | Rev Growth: {grw}\nDebt/Equity: {d2e} | Free Cash Flow: {fcf} | Insider Holding: {ins}\n---\n"
                    except Exception as e: st.error(f"Skipping {tkr}: {str(e)}")
                    progress_bar.progress((idx + 1) / len(selected_tickers))
            
            with st.expander("🔍 View Raw Extracted Dossier"): st.text(combined_stock_data)
            
            if not groq_api_key: st.error("🔑 Provide Groq Key in sidebar.")
            else:
                with st.spinner("Handing metrics over to Groq..."):
                    try:
                        client = Groq(api_key=groq_api_key)
                        prompt = f"You are a quant hedge fund CIO. Analyze this institutional fundamental dossier:\n{combined_stock_data}\n\nCRITICAL FORMAT RULES:\n- Do NOT write long text reports.\n- Output ONLY a clean Markdown Table comparing the key assets, followed by exactly ONE short two-sentence tactical summary picking the absolute 'Best Buy' winner based on balance sheet strengths and its single main risk trap."
                        completion = client.chat.completions.create(model=selected_model, messages=[{"role": "user", "content": prompt}], temperature=0.2)
                        st.subheader("🏆 Institutional Quantitative Investment Report")
                        st.markdown(completion.choices[0].message.content)
                    except Exception as e: st.error(f"Groq Interface Issue: {str(e)}")
else: st.info("💡 Drop a tracking CSV file or paste symbols above to initialize the pipeline.")

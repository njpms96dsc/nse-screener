import streamlit as st
import io, csv, requests
from groq import Groq

st.set_page_config(page_title="Hybrid Screener", layout="wide")
st.title("📊 AI-Powered Technical & Fundamental NSE Screener")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("🔑 Credentials & Settings")
groq_api_key = st.sidebar.text_input("Groq API Key", type="password")
selected_model = st.sidebar.selectbox("LLM Brain", ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"])

st.sidebar.subheader("📈 Volume Spike Settings")
run_daily = st.sidebar.checkbox("Scan Daily Spikes (20d)", value=True)
daily_thresh = st.sidebar.slider("Daily Multiplier", 1.0, 5.0, 2.0, 0.5)
run_intraday = st.sidebar.checkbox("Scan Intraday Spikes (5m)", value=False)
intraday_thresh = st.sidebar.slider("Intraday Multiplier", 1.0, 5.0, 2.0, 0.5)

# --- STEP 1: PORTFOLIO INTAKE ---
st.subheader("📁 Step 1: Provide Your Tickers")
input_method = st.radio("Input method:", ["Upload CSV File", "Paste Symbols Text Box"])
raw_symbols = []

if input_method == "Upload CSV File":
    uploaded_file = st.file_uploader("Upload stock list file:", type=None)
    if uploaded_file is not None:
        try:
            # Safe defensive parsing block to handle file conversions cleanly
            text_data = uploaded_file.getvalue().decode("utf-8", errors="ignore")
            reader = csv.reader(io.StringIO(text_data))
            for row in reader:
                # Explicit check verifying the row exists and has at least 3 columns
                if row and len(row) >= 3:
                    sym = str(row[2]).strip().replace('"', '').upper()
                    if sym and sym not in ['SYMBOL', 'TICKER', 'NAME', '']:
                        raw_symbols.append(sym)
            raw_symbols = list(set(raw_symbols))
            if raw_symbols: st.success(f"Parsed! Extracted **{len(raw_symbols)}** symbols from column 3.")
            else: st.error("No valid ticker strings discovered in the 3rd column.")
        except Exception as e: st.error(f"File reading issue: {str(e)}")
else:
    text_input = st.text_area("Paste symbols (split by space/comma):", value="SBIN, RELIANCE, INFY")
    if text_input: raw_symbols = list(set([s.strip().upper() for s in text_input.replace(",", " ").split() if s.strip()]))

if raw_symbols:
    formatted_tickers = [s if s.endswith('.NS') else f"{s}.NS" for s in raw_symbols if s]
    st.write(f"Total Unique Tickers Tracked: **{len(formatted_tickers)}**")
    
    # --- STEP 2: QUANT SELECTION ---
    st.subheader("🎯 Step 2: Select Targets for Synthesis")
    selected_tickers = st.multiselect("Choose targets to scan:", options=formatted_tickers, default=formatted_tickers[:min(3, len(formatted_tickers))])
    
    if not selected_tickers:
        st.warning("⚠️ Choose at least one target stock above to activate the engine.")
    else:
        if st.button("Activate Hybrid Quantum Engine 🚀"):
            combined_stock_data, progress_bar = "", st.progress(0)
            # Use browser headers to mask cloud server nodes completely
            hdrs = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            
            with st.spinner("Executing Technical & Fundamental Fusion Scan..."):
                for idx, tkr in enumerate(selected_tickers):
                    try:
                        # LAYER 1: FETCH PREMIUM FUNDAMENTAL DATA IN ONE SECURE GET CALL
                        url = f"https://yahoo.com{tkr}?modules=defaultKeyStatistics,financialData,summaryDetail"
                        res = requests.get(url, headers=hdrs, timeout=10).json()
                        name, prc, roe, pb, fcf, ins, div, pe, fpe, d2e, mgn, grw = tkr.replace('.NS',''),'N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A'
                        
                        if 'quoteSummary' in res and res['quoteSummary']['result']:
                            r = res['quoteSummary']['result'][0]
                            f, s, d = r.get('financialData',{}), r.get('defaultKeyStatistics',{}), r.get('summaryDetail',{})
                            # Parse High-Alpha Quant values cleanly
                            prc = f.get('currentPrice',{}).get('raw') or d.get('previousClose',{}).get('raw') or 'N/A'
                            pe = d.get('trailingPE',{}).get('raw') or d.get('forwardPE',{}).get('raw') or 'N/A'
                            fpe = d.get('forwardPE',{}).get('raw') or 'N/A'
                            d2e = f.get('debtToEquity',{}).get('raw')
                            if d2e is None: d2e = "N/A (Banking Layout)" if "sbin" in tkr.lower() else "N/A"
                            mgn = f.get('profitMargins',{}).get('raw') or f.get('operatingMargins',{}).get('raw') or 'N/A'
                            grw = f.get('revenueGrowth',{}).get('raw') or s.get('quarterlyRevenueGrowth',{}).get('raw') or 'N/A'
                            roe = f.get('returnOnEquity',{}).get('raw') or 'N/A'
                            pb = d.get('priceToBook',{}).get('raw') or s.get('priceToBook',{}).get('raw') or 'N/A'
                            fcf = f.get('freeCashflow',{}).get('raw') or 'N/A'
                            ins = s.get('heldPercentInsiders',{}).get('raw') or 'N/A'
                            div = d.get('dividendYield',{}).get('raw') or 'N/A'
                            # Percentage standardizing formats
                            if isinstance(mgn, float): mgn = f"{round(mgn*100,2)}%"
                            if isinstance(grw, float): grw = f"{round(grw*100,2)}%"
                            if isinstance(roe, float): roe = f"{round(roe*100,2)}%"
                            if isinstance(ins, float): ins = f"{round(ins*100,2)}%"
                            if isinstance(div, float): div = f"{round(div*100,2)}%"
                            if isinstance(fcf, (int, float)): fcf = f"INR {fcf:,.2f}"

                        # LAYER 2: RUN PYDROID-STYLE VOLUME SPIKE CHECK MATH
                        d_spike, i_spike = "NORMAL VOLUME", "NORMAL VOLUME"
                        if run_daily:
                            d_res = requests.get(f"https://yahoo.com{tkr}?interval=1d&range=1mo", headers=hdrs, timeout=10).json()
                            if 'chart' in d_res and d_res['chart']['result']:
                                v = [vol for vol in d_res['chart']['result'][0]['indicators']['quote'][0].get('volume', []) if vol is not None]
                                if len(v) >= 2 and (sum(v[:-1])/len(v[:-1])) > 0 and (v[-1]/(sum(v[:-1])/len(v[:-1]))) >= daily_thresh:
                                    d_spike = f"💥 SPIKE ({round(v[-1]/(sum(v[:-1])/len(v[:-1])),2)}x)"
                        if run_intraday:
                            i_res = requests.get(f"https://yahoo.com{tkr}?interval=5m&range=1d", headers=hdrs, timeout=10).json()
                            if 'chart' in i_res and i_res['chart']['result']:
                                v = [vol for vol in i_res['chart']['result'][0]['indicators']['quote'][0].get('volume', []) if vol is not None]
                                if len(v) >= 2 and (sum(v[:-1])/len(v[:-1])) > 0 and (v[-1]/(sum(v[:-1])/len(v[:-1]))) >= intraday_thresh:
                                    i_spike = f"⚡ 5M SPIKE ({round(v[-1]/(sum(v[:-1])/len(v[:-1])),2)}x)"

                        # COLLATED ATTRIBUTE DOSSIER
                        combined_stock_data += f"== {name} ({tkr}) ==\nVol Daily: {d_spike} | 5m: {i_spike}\nPrc: {prc} | PE: {pe} | FwdPE: {fpe} | P/B: {pb}\nROE: {roe} | Margin: {mgn} | Growth: {grw}\nDebt: {d2e} | FCF: {fcf} | Insider: {ins} | Div: {div}\n---\n"
                    except Exception as e: st.error(f"Skipping {tkr}: {str(e)}")
                    progress_bar.progress((idx + 1) / len(selected_tickers))
            
            with st.expander("🔍 View Raw Extracted Dossier"): st.text(combined_stock_data)
            
            # --- STEP 3: ARTIFICIAL HEURISTIC REASONING ---
            if not groq_api_key: st.error("🔑 Provide Groq Key in sidebar.")
            else:
                with st.spinner("Handing over data to Groq..."):
                    try:
                        client = Groq(api_key=groq_api_key)
                        prompt = f"You are a quant hedge fund CIO. Analyze this financial/momentum data dossier:\n{combined_stock_data}\n\nCRITICAL OUTPUT FORMAT RULES:\n- Do NOT write a paragraphs or reports.\n- Output ONLY a clean Markdown Table comparing the key assets, followed by exactly ONE short two-sentence tactical summary picking the absolute 'Best Buy' winner and its single main risk trap."
                        completion = client.chat.completions.create(model=selected_model, messages=[{"role": "user", "content": prompt}], temperature=0.2)
                        st.subheader("🏆 Institutional Quantitative Investment Report")
                        st.markdown(completion.choices[0].message.content)
                    except Exception as e: st.error(f"Groq Interface Issue: {str(e)}")
else: st.info("💡 Drop a tracking CSV file or paste symbols above to initialize the pipeline.")

import streamlit as st
import io, csv, requests
from groq import Groq

st.set_page_config(page_title="Hybrid Screener", layout="wide")
st.title("📊 AI-Powered Technical & Fundamental NSE Screener")

st.sidebar.header("🔑 Credentials & Settings")
groq_api_key = st.sidebar.text_input("Groq API Key", type="password")
selected_model = st.sidebar.selectbox("LLM Brain", ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"])

st.sidebar.subheader("📈 Volume Spike Settings")
run_daily = st.sidebar.checkbox("Scan Daily Spikes (20d)", value=True)
daily_thresh = st.sidebar.slider("Daily Multiplier", 1.0, 5.0, 2.0, 0.5)

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
        if st.button("Activate Hybrid Quantum Engine 🚀"):
            combined_stock_data, progress_bar = "", st.progress(0)
            hdrs = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            
            with st.spinner("Executing Technical & Fundamental Fusion Scan..."):
                for idx, tkr in enumerate(selected_tickers):
                    try:
                        # MODERNIZED CALL: Query the active chart endpoint natively
                        c_url = f"https://yahoo.com{tkr}?interval=1d&range=1mo"
                        c_res = requests.get(c_url, headers=hdrs, timeout=10).json()
                        
                        name = tkr.replace('.NS','')
                        prc, d_spike, prev_close = 'N/A', 'NORMAL VOLUME', 'N/A'
                        
                        if 'chart' in c_res and c_res['chart']['result']:
                            meta = c_res['chart']['result'][0].get('meta', {})
                            prc = meta.get('regularMarketPrice') or 'N/A'
                            prev_close = meta.get('chartPreviousClose') or 'N/A'
                            
                            # Re-engineering Pydroid chart volume accumulation checks
                            v = [vol for vol in c_res['chart']['result'][0]['indicators']['quote'][0].get('volume', []) if vol is not None]
                            if len(v) >= 2:
                                avg_vol = sum(v[:-1]) / len(v[:-1])
                                if avg_vol > 0 and (v[-1] / avg_vol) >= daily_thresh:
                                    d_spike = f"💥 SPIKE ({round(v[-1]/avg_vol, 2)}x)"
                        
                        combined_stock_data += f"== {name} ({tkr}) ==\nPrice: INR {prc} | Prev Close: INR {prev_close}\nVolume Status: {d_spike}\n---\n"
                    except Exception as e: st.error(f"Skipping {tkr}: {str(e)}")
                    progress_bar.progress((idx + 1) / len(selected_tickers))
            
            with st.expander("🔍 View Raw Extracted Dossier"): st.text(combined_stock_data)
            
            if not groq_api_key: st.error("🔑 Provide Groq Key in sidebar.")
            else:
                with st.spinner("Handing over data to Groq..."):
                    try:
                        client = Groq(api_key=groq_api_key)
                        prompt = f"You are a quant hedge fund CIO. Analyze this financial/momentum data dossier:\n{combined_stock_data}\n\nCRITICAL FORMAT RULES:\n- Output ONLY a clean Markdown Table comparing the key assets, followed by exactly ONE short two-sentence tactical summary picking the absolute 'Best Buy' winner and its single main risk trap."
                        completion = client.chat.completions.create(model=selected_model, messages=[{"role": "user", "content": prompt}], temperature=0.2)
                        st.subheader("🏆 Institutional Quantitative Investment Report")
                        st.markdown(completion.choices[0].message.content)
                    except Exception as e: st.error(f"Groq Interface Issue: {str(e)}")
else: st.info("💡 Drop a tracking CSV file or paste symbols above to initialize the pipeline.")

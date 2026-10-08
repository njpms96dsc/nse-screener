import streamlit as str
import yfinance as yf
import os
from dotenv import load_dotenv
from groq import Groq
import database as db  # Imports your custom database cache

# Load environment variables (for local testing, Render handles this automatically)
load_dotenv()

# Initialize the SQLite database table
db.init_db()

# Initialize Groq Client safely using environment variable
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# --- STREAMLIT UI ---
str.title("📊 Smart Stock Insights")
str.write("Get instant stock data powered by live cache and AI reasoning.")

# User Input for Stock Ticker
ticker_input = str.text_input("Enter Stock Ticker (e.g., AAPL, TSLA, INFY):", "").upper().strip()

if ticker_input:
    str.subheader(f"Analysis for {ticker_input}")
    
    # 1. Try to get price from local database cache first
    price = db.get_cached_price(ticker_input)
    
    if price is not None:
        str.info(f"💡 Fetching data from local database cache (Fresh within 15 mins).")
    else:
        # 2. Cache expired or missing -> Fetch from yfinance
        str.warning(f"🔄 Cache missed or expired. Fetching live data from yfinance...")
        try:
            stock = yf.Ticker(ticker_input)
            # Get latest closing or current price
            todays_data = stock.history(period='1d')
            if not todays_data.empty:
                price = todays_data['Close'].iloc[-1]
                # Save the new price to database cache
                db.set_cached_price(ticker_input, price)
            else:
                str.error("Could not find recent price data for this ticker.")
        except Exception as e:
            str.error(f"Error fetching data from yfinance: {e}")
            
    # Display the price if we successfully got it
    if price is not None:
        str.metric(label="Current Estimated Price", value=f"${price:,.2f}")
        
        # 3. Generate AI Summary using Groq
        if client:
            with str.spinner("🤖 AI is analyzing market sentiment..."):
                try:
                    prompt = f"Provide a brief, 3-bullet-point summary of the recent market sentiment or outlook for the stock ticker {ticker_input}. The current price is around ${price:.2f}."
                    
                    completion = client.chat.completions.create(
                        model="llama-3.1-8b-instant",  # Fast & reliable model
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7,
                        max_tokens=150
                    )
                    
                    ai_response = completion.choices[0].message.content
                    str.markdown("### 🤖 AI Market Insights")
                    str.write(ai_response)
                    
                except Exception as ai_err:
                    str.error(f"Could not load AI insights: {ai_err}")
        else:
            str.error("Groq API key missing. Please configure GROQ_API_KEY in your environment.")

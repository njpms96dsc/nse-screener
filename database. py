import sqlite3
from datetime import datetime, timedelta

DB_NAME = "stocks.db"

def init_db():
    """Creates the database table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_cache (
            ticker TEXT PRIMARY KEY,
            price REAL,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_cached_price(ticker):
    """Retrieves the price if it was updated within the last 15 minutes."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT price, timestamp FROM stock_cache WHERE ticker = ?", (ticker.upper(),))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        price, timestamp_str = row
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        # Check if the data is fresh (less than 15 minutes old)
        if datetime.now() - timestamp < timedelta(minutes=15):
            return price
    return None

def set_cached_price(ticker, price):
    """Saves or updates the stock price with a current timestamp."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT OR REPLACE INTO stock_cache (ticker, price, timestamp)
        VALUES (?, ?, ?)
    ''', (ticker.upper(), price, now_str))
    conn.commit()
    conn.close()


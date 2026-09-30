import os
import csv
import time
import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_downloads_path():
    """Detects standard Android Downloads path or fallback."""
    primary_download = '/storage/emulated/0/Download'
    if os.path.exists(primary_download):
        return primary_download
    return os.path.expanduser('~/Download')

def select_csv_file(download_dir):
    """Lists CSV files in Downloads and lets user select one by number."""
    if not os.path.exists(download_dir):
        print(f"Error: Directory not found: {download_dir}")
        return None

    csv_files = [f for f in os.listdir(download_dir) if f.lower().endswith('.csv')]
    
    if not csv_files:
        print(f"No CSV files found in: {download_dir}")
        return None

    print("\n--- STEP 1: SELECT CSV FILE ---")
    for idx, fname in enumerate(csv_files, start=1):
        print(f"{idx}. {fname}")
    
    while True:
        try:
            choice = int(input("\nSelect a CSV file number to scan: "))
            if 1 <= choice <= len(csv_files):
                selected_file = csv_files[choice - 1]
                return os.path.join(download_dir, selected_file)
            else:
                print("Invalid choice. Try again.")
        except ValueError:
            print("Please enter a valid number.")

def load_symbols_from_3rd_column(file_path):
    """Extracts unique stock symbols from the 3rd column (Index 2)."""
    symbols = []
    print(f"\nLoading symbols from: {os.path.basename(file_path)}")
    
    try:
        with open(file_path, mode='r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 3:
                    symbol = row[2].strip().replace('"', '')
                    if symbol and symbol.lower() not in ['symbol', 'ticker', 'name']:
                        symbols.append(symbol)
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

    return list(set(symbols))

def prompt_timeframe_config(name):
    """Prompts whether to enable a timeframe and sets its threshold."""
    while True:
        choice = input(f"Do you want to scan {name} charts? (y/n) [default: y]: ").strip().lower()
        if choice in ['', 'y', 'yes']:
            enabled = True
            break
        elif choice in ['n', 'no']:
            enabled = False
            return False, 0.0
        else:
            print("Please enter 'y' or 'n'.")
            
    # If enabled, prompt for multiplier
    user_input = input(f"  -> Enter volume multiplier for {name} [default: 2.0]: ").strip()
    if not user_input:
        thresh = 2.0
    else:
        try:
            thresh = float(user_input)
            if thresh <= 0:
                thresh = 2.0
        except ValueError:
            print("  -> Invalid input. Using default 2.0x")
            thresh = 2.0
            
    return enabled, thresh

def fetch_chart_data(symbol, interval="1d", range_period="1mo"):
    formatted_symbol = symbol.strip().upper()
    if not formatted_symbol.endswith('.NS'):
        formatted_symbol += '.NS'
        
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{formatted_symbol}?interval={interval}&range={range_period}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return None
        
        data = response.json()
        result = data['chart']['result'][0]
        
        raw_volumes = result['indicators']['quote'][0].get('volume', [])
        return [v for v in raw_volumes if v is not None]
    except Exception:
        return None

def check_volume_spike(volumes, lookback=20, spike_threshold=2.0):
    if not volumes or len(volumes) < 2:
        return False, 0, 0
    
    latest_volume = volumes[-1]
    historical_volumes = volumes[-lookback-1:-1] if len(volumes) > lookback else volumes[:-1]
    
    if not historical_volumes:
        return False, 0, 0
    
    avg_volume = sum(historical_volumes) / len(historical_volumes)
    if avg_volume == 0:
        return False, 0, 0
    
    ratio = latest_volume / avg_volume
    return ratio >= spike_threshold, latest_volume, avg_volume

def main():
    downloads_path = get_downloads_path()
    
    # 1. File selection
    selected_csv = select_csv_file(downloads_path)
    if not selected_csv:
        return

    # 2. Timeframe Selection Prompts
    print("\n--- STEP 2: SELECT TIMEFRAMES TO SCAN ---")
    run_intraday, intraday_thresh = prompt_timeframe_config("Intraday (5m)")
    run_daily, daily_thresh = prompt_timeframe_config("Daily")

    if not run_intraday and not run_daily:
        print("\nNo timeframes selected. Exiting scan.")
        return

    # 3. Load stock symbols
    symbols = load_symbols_from_3rd_column(selected_csv)
    if not symbols:
        print("No valid symbols found in the selected CSV.")
        return

    print(f"\nLoaded {len(symbols)} unique symbols.")
    
    active_modes = []
    if run_daily: active_modes.append(f"Daily >= {daily_thresh}x")
    if run_intraday: active_modes.append(f"Intraday (5m) >= {intraday_thresh}x")
    print("Active Scan Settings: " + " | ".join(active_modes) + "\n")
    
    spikes_found = []

    for symbol in symbols:
        print(f"Scanning {symbol}...", end=" ")
        
        daily_spike, d_curr, d_avg = False, 0, 0
        intraday_spike, i_curr, i_avg = False, 0, 0
        
        # Daily Volume Check (if enabled)
        if run_daily:
            daily_vols = fetch_chart_data(symbol, interval="1d", range_period="1mo")
            daily_spike, d_curr, d_avg = check_volume_spike(daily_vols, lookback=20, spike_threshold=daily_thresh)
        
        # Intraday (5m) Volume Check (if enabled)
        if run_intraday:
            intraday_vols = fetch_chart_data(symbol, interval="5m", range_period="1d")
            intraday_spike, i_curr, i_avg = check_volume_spike(intraday_vols, lookback=12, spike_threshold=intraday_thresh)
        
        if daily_spike or intraday_spike:
            status = []
            if daily_spike:
                status.append(f"Daily ({d_curr:,} vs Avg {int(d_avg):,})")
            if intraday_spike:
                status.append(f"5m Intraday ({i_curr:,} vs Avg {int(i_avg):,})")
            
            print(f" SPIKE DETECTED! -> " + " | ".join(status))
            spikes_found.append({'symbol': symbol, 'daily': daily_spike, 'intraday': intraday_spike})
        else:
            print("Normal")
        
        time.sleep(0.3)

    print("\n" + "="*50)
    print(f"SCAN COMPLETE: {len(spikes_found)} stock(s) met volume conditions")
    print("="*50)
    for item in spikes_found:
        tags = []
        if item['daily']: tags.append("DAILY")
        if item['intraday']: tags.append("INTRADAY")
        print(f"• {item['symbol']} [{', '.join(tags)}]")

if __name__ == "__main__":
    main()
#vol

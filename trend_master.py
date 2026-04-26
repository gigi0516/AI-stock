import os
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta

def run_full_strategy():
    # 從環境變數讀取 Token 
    token = os.environ.get('FINMIND_TOKEN')
    api = DataLoader()
    
    if token:
        # 修正點：將 api.login 改為 api.login_by_token
        api.login_by_token(token=token) 
    
    print(f"🚀 trend_master (執行時間: {datetime.now()}) [cite: 58]")

    # 設定時間範圍，抓取足夠計算 MA60 的資料量 [cite: 61, 62]
    start_date = (datetime.now() - timedelta(days=120)).strftime("%Y-%m-%d")

    # --- 第一層 & 第二層：技術面與成交量 [cite: 59, 63] ---
    df_price = api.taiwan_stock_daily_adj(start_date=start_date) [cite: 76]
    
    # 計算 MA20 [cite: 62]
    df_price['MA20'] = df_price.groupby('stock_id')['close'].transform(lambda x: x.rolling(window=20).mean())
    
    latest_price = df_price.groupby('stock_id').tail(1).copy()
    
    # 邏輯：股價 > MA20 且 成交量 > 1000 [cite: 60, 64]
    tech_mask = (latest_price['close'] > latest_price['MA20']) & (latest_price['Volume'] > 1000)
    tech_passed_list = latest_price[tech_mask]['stock_id'].tolist()

    # --- 第三層：籌碼面 (投信連買) [cite: 66, 67] ---
    # 這裡先過濾出技術面合格的標的，減少 API 呼叫負擔，縮短時間差 
    df_inst = api.taiwan_stock_institutional_investors_buy_sell(start_date=(datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")) [cite: 76]
    inst_passed = df_inst[(df_inst['buy_sell_center'] == 'Investment_Trust') & (df_inst['Quantity'] > 0)]
    inst_passed_list = inst_passed['stock_id'].unique().tolist()

    # --- 第四層：基本面 (營收 YoY 為正) [cite: 69, 70] ---
    potential_candidates = list(set(tech_passed_list) & set(inst_passed_list))
    
    final_list = []
    for stock_id in potential_candidates:
        df_revenue = api.taiwan_stock_month_revenue(stock_id=stock_id, start_date=start_date) [cite: 76]
        if not df_revenue.empty and df_revenue.iloc[-1]['revenue_year_growth_rate'] > 0:
            final_list.append(stock_id)

    return final_list

if __name__ == "__main__":
    candidates = run_full_strategy()
    print(f"✅ 最終精選名單: {candidates} ")

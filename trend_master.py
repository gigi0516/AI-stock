import os
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta

def run_full_strategy():
    # 從環境變數讀取 Token，增加安全度與自動化效率 
    token = os.environ.get('FINMIND_TOKEN')
    api = DataLoader()
    if token:
        api.login(token=token)
    
    print(f"🚀 啟動全能趨勢過濾機器人 (執行時間: {datetime.now()})")

    # 設定時間範圍
    start_date = (datetime.now() - timedelta(days=120)).strftime("%Y-%m-%d")

    # --- 第一層 & 第二層：技術面與成交量 [cite: 59, 63] ---
    df_price = api.taiwan_stock_daily_adj(start_date=start_date)
    # 計算 MA20 [cite: 62]
    df_price['MA20'] = df_price.groupby('stock_id')['close'].transform(lambda x: x.rolling(window=20).mean())
    
    latest_price = df_price.groupby('stock_id').tail(1).copy()
    
    # 過濾：股價 > MA20 且 成交量 > 1000 [cite: 60, 64]
    tech_mask = (latest_price['close'] > latest_price['MA20']) & (latest_price['Volume'] > 1000)
    tech_passed_df = latest_price[tech_mask]
    tech_passed_list = tech_passed_df['stock_id'].tolist()

    # --- 第三層：籌碼面 (法人連續買超) [cite: 66, 67] ---
    df_inst = api.taiwan_stock_institutional_investors_buy_sell(start_date=(datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"))
    # 找出投信買超股 [cite: 67]
    inst_passed = df_inst[df_inst['buy_sell_center'] == 'Investment_Trust']
    inst_passed_list = inst_passed[inst_passed['Quantity'] > 0]['stock_id'].unique().tolist()

    # --- 第四層：基本面 (營收 YoY 與 EPS) [cite: 69, 70, 71] ---
    # 這裡我們取交集，確保標的同時符合技術與籌碼面
    potential_candidates = list(set(tech_passed_list) & set(inst_passed_list))
    
    final_list = []
    for stock_id in potential_candidates:
        # 檢查營收年增率 (YoY) 是否為正 [cite: 70]
        df_revenue = api.taiwan_stock_month_revenue(stock_id=stock_id, start_date=start_date)
        if not df_revenue.empty and df_revenue.iloc[-1]['revenue_year_growth_rate'] > 0:
            final_list.append(stock_id)

    return final_list

if __name__ == "__main__":
    candidates = run_full_strategy()
    print(f"✅ 最終精選名單: {candidates}")

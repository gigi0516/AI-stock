import os
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta

def run_full_strategy():
    token = os.environ.get('FINMIND_TOKEN')
    api = DataLoader()
    if token:
        api.login_by_token(token)
    
    # 設定時間：抓取最近 3 天的資料來確認 MA 趨勢與成交量 [cite: 58, 62]
    today = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

    print(f"🚀 啟動全能趨勢過濾機器人... [cite: 56]")

    # --- 第一層 & 第二層：技術面與成交量 (優化：使用全市場日資料)  ---
    # 修正點：改用支援全市場抓取的 API 介面
    df_price = api.taiwan_stock_daily(
        start_date=start_date,
        end_date=today
    ) [cite: 76]

    # 計算 MA20 [cite: 62]
    df_price['MA20'] = df_price.groupby('stock_id')['close'].transform(lambda x: x.rolling(window=20, min_periods=1).mean())
    
    # 取得最新一筆交易日資料 [cite: 58]
    latest_data = df_price.groupby('stock_id').tail(1).copy()
    
    # 篩選條件：股價 > MA20 [cite: 60] 且 成交量 > 1000 [cite: 64]
    tech_mask = (latest_data['close'] > latest_data['MA20']) & (latest_data['Volume'] > 1000)
    tech_passed_list = latest_data[tech_mask]['stock_id'].tolist()
    
    print(f"🔎 技術面過濾完成，剩餘 {len(tech_passed_list)} 檔標的 [cite: 72]")

    # --- 第三層：籌碼面 (投信買超) [cite: 66, 67] ---
    # 僅針對通過技術面篩選的標的進行查詢，減少 API 耗時 [cite: 3]
    final_candidates = []
    # (此處建議先取前 50 檔測試，避免 GitHub Actions 執行過久)
    for stock_id in tech_passed_list[:50]: 
        df_inst = api.taiwan_stock_institutional_investors_buy_sell(
            stock_id=stock_id,
            start_date=(datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        ) [cite: 76]
        
        # 判斷投信是否有買超動作 [cite: 67]
        if not df_inst.empty and df_inst[df_inst['buy_sell_center'] == 'Investment_Trust']['Quantity'].sum() > 0:
            final_candidates.append(stock_id)

    return final_candidates

if __name__ == "__main__":
    candidates = run_full_strategy()
    print(f"✅ 最終精選名單: {candidates} [cite: 72]")

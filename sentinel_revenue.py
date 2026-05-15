import os
import json
import firebase_admin
from firebase_admin import credentials, db
from FinMind.data import DataLoader
from datetime import datetime, timedelta, timezone


def run_sentinel_strategy():
    tw_now = get_taiwan_time()
    print(f"--- 🚀 機器人一號：持股營收哨兵啟動 ({tw_now.strftime('%Y-%m-%d')}) ---")

    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN', '')

    # --- 這裡最重要！要把清單拿回來 ---
    # 確保這一行在 for 迴圈之前
    my_stocks = ["2330", "2337", "2454", "2308", "2317", "7794", "2072"]
            start_date = (tw_now - timedelta(days=180)).strftime("%Y-%m-%d")
    qualified_candidates = []
    
    # 開始跑迴圈
    for stock_id in my_stocks:
        try:
            df = api.taiwan_stock_month_revenue(
                stock_id=stock_id,
                start_date=start_date,
                token=token
            )
     for stock_id in my_stocks:
            try:
                df = api.taiwan_stock_month_revenue(
                    stock_id=stock_id,
                    start_date=start_date,
                    token=token
                )
                
                if df.empty or len(df) < 4:
                    print(f"⚠️ {stock_id}：資料不足或為空 (抓到 {len(df)} 筆)") # 加這行診斷
                    continue
                
                df = df.sort_values('date')
                recent_4 = df.tail(4)
                
                # --- 新增這兩行：這是診斷關鍵！ ---
                yoy_list = recent_4['revenue_year_growth_percent'].tolist()
                print(f"🔍 檢查 {stock_id} 最近 4 月 YoY: {yoy_list}")
                # -------------------------------

                is_qualified = True
                for yoy in yoy_list:
                    if yoy < 1:
                        is_qualified = False
                        break
                
                status = "🔥" if is_qualified else "⚪"
                name = df.iloc[-1].get('stock_name', stock_id)
                qualified_candidates.append(f"{status} {stock_id} {name}")
                
                # 加這行讓你在 GitHub Log 看到每檔的結果
                print(f"{status} {stock_id} 判定完成") 

            except Exception as e: 
                print(f"❌ {stock_id} 發生錯誤: {e}") # 這裡原本是 print(e)，建議改這樣比較清楚

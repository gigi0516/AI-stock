import os
import json
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
from FinMind.data import DataLoader
from datetime import datetime, timedelta, timezone

def get_taiwan_time():
    """獲取精準的台灣時間"""
    # GitHub 伺服器是 UTC，我們手動加 8 小時轉為台灣時間
    tw_time = datetime.now(timezone.utc) + timedelta(hours=8)
    return tw_time

def run_full_strategy():
    tw_now = get_taiwan_time()
    print(f"⏰ 當前台灣時間: {tw_now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    token = os.environ.get('FINMIND_TOKEN')
    api = DataLoader()
    if token: api.login_by_token(token)
    
    # 邏輯優化：設定結束日期為今天，但 start_date 設遠一點
    # 這樣 FinMind API 會自動回傳「到今天為止最新的所有資料」
    end_date = tw_now.strftime("%Y-%m-%d")
    start_date = (tw_now - timedelta(days=70)).strftime("%Y-%m-%d")

    raw_list = [
        '3481', '2409', '2303', '2337', '2344', '1802', '2313', '4958', '2408', 
        '6770', '2367', '2317', '2312', '1717', '3189', '2542', '1303', '2399', 
        '6176', '2388', '2330', '2436', '2356', '2002', '3231', '1309', '2485', 
        '8150', '2449', '2324', '4927', '2327', '2316', '2355', '6285', '3711', 
        '2464', '1301', '2301', '2353', '2618', '3019', '3338', '3045'
    ]
    
    final_candidates = []
    print(f"🚀 掃描中...")

    for stock_id in raw_list:
        try:
            # 獲取歷史資料
            df_price = api.taiwan_stock_daily(stock_id=stock_id, start_date=start_date, end_date=end_date)
            
            # 如果是週末，df_price 的最後一筆會自動停在「上週五」
            if len(df_price) < 20: continue
            
            df_price['MA20'] = df_price['close'].rolling(window=20).mean()
            latest = df_price.iloc[-1]
            
            # --- 判斷條件 ---
            # 1. 股價 > MA20
            # 2. 法人近三日合計買超 > 0
            if latest['close'] > latest['MA20']:
                df_inst = api.taiwan_stock_institutional_investors_buy_sell(
                    stock_id=stock_id, 
                    start_date=(tw_now - timedelta(days=7)).strftime("%Y-%m-%d")
                )
                if not df_inst.empty and df_inst['Quantity'].sum() > 0:
                    df_rev = api.taiwan_stock_month_revenue(
                        stock_id=stock_id, 
                        start_date=(tw_now - timedelta(days=60)).strftime("%Y-%m-%d")
                    )
                    if not df_rev.empty and df_rev.iloc[-1]['revenue_year_growth_rate'] > 0:
                        final_candidates.append(stock_id)
                        print(f"🎯 找到符合標的: {stock_id} (最後交易日: {latest['date']})")
        except:
            continue
            
    return final_candidates

# --- Firebase 上傳與主程式部分維持原樣 ---

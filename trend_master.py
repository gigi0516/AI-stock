import os
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta

def run_full_strategy():
    token = os.environ.get('FINMIND_TOKEN')
    api = DataLoader()
    if token: api.login_by_token(token)
    
    # 1. 導入你提供的成交量前 100 名單 (已轉換為 FinMind 格式)
    # 過濾掉權證與非個股標的，專注於個股篩選
    raw_list = [
        '3481', '2409', '2303', '2337', '2344', '1802', '2313', '4958', '2408', 
        '6770', '2367', '2317', '2312', '1717', '3189', '2542', '1303', '2399', 
        '6176', '2388', '2330', '2436', '2356', '2002', '3231', '1309', '2485', 
        '8150', '2449', '2324', '4927', '2327', '2316', '2355', '6285', '3711', 
        '2464', '1301', '2301', '2353', '2618', '3019', '3338', '3045'
    ]
    
    print(f"🚀 啟動全能趨勢過濾機器人 (掃描成交量熱門股: {len(raw_list)} 檔)...")
    final_candidates = []

    for stock_id in raw_list:
        try:
            # --- 第一 & 二層：技術面與成交量 ---
            df_price = api.taiwan_stock_daily(stock_id=stock_id, start_date='2026-03-01')
            if len(df_price) < 20: continue
            
            # 計算 MA20
            df_price['MA20'] = df_price['close'].rolling(window=20).mean()
            latest = df_price.iloc[-1]
            
            # 條件：股價 P > MA20 (文件規定)
            if latest['close'] > latest['MA20']:
                
              # 第三層：籌碼面 [cite: 66]
                # 優化：只要近期法人（外資或投信）有買超即可 [cite: 67]
                df_inst = api.taiwan_stock_institutional_investors_buy_sell(stock_id=stock_id, start_date=(datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"))
                total_buy = df_inst['Quantity'].sum()
            if total_buy > 0:
                # 基本面：保留營收 YoY > 0 的安全性門檻 [cite: 70]
                # ... 後續邏輯 ...
                    # --- 第四層：基本面 (營收 YoY) ---
                    df_rev = api.taiwan_stock_month_revenue(
                        stock_id=stock_id, 
                        start_date=(datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
                    )
                    # 條件：YoY 為正 (文件規定)
                    if not df_rev.empty and df_rev.iloc[-1]['revenue_year_growth_rate'] > 0:
                        final_candidates.append(stock_id)
                        print(f"🎯 符合全能趨勢過濾標的: {stock_id}")
        except:
            continue
            
    return final_candidates

if __name__ == "__main__":
    candidates = run_full_strategy()
    print(f"✅ 最終精選名單: {candidates}")

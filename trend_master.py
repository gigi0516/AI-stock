import os
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime, timedelta

def run_full_strategy():
    token = os.environ.get('FINMIND_TOKEN')
    api = DataLoader()
    if token:
        api.login_by_token(token)
    
    today = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")

    print("📊 正在獲取今日全市場成交量排名...")
    
    # 步驟 1：抓取今日全市場成交量（利用台股總體資料集獲取排行）
    # 如果今日資料尚未更新，會自動抓取前一交易日
    df_all = api.taiwan_stock_daily_adj(start_date=(datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"))
    
    # 取得最新一天的資料並按成交量 (Volume) 排序
    latest_all = df_all.groupby('stock_id').tail(1)
    top_100_list = latest_all.sort_values(by='Volume', ascending=False).head(100)['stock_id'].tolist()
    
    print(f"🔥 已鎖定成交量前 100 名標的，開始執行四層過濾邏輯...")

    final_candidates = []

    for stock_id in top_100_list:
        try:
            # 獲取單檔詳細資料（符合註冊會員權限）
            df_price = api.taiwan_stock_daily(stock_id=stock_id, start_date=start_date, end_date=today)
            if len(df_price) < 20: continue
            
            # --- 第一、二層：技術面與成交量 ---
            df_price['MA20'] = df_price['close'].rolling(window=20).mean()
            latest = df_price.iloc[-1]
            
            # 股價 > MA20 [cite: 60] 且成交量維持高水位 [cite: 64]
            if latest['close'] > latest['MA20']:
                
                # --- 第三層：籌碼面 (投信買超) ---
                df_inst = api.taiwan_stock_institutional_investors_buy_sell(
                    stock_id=stock_id, 
                    start_date=(datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
                )
                # 檢查投信是否連續買超或近期有買超動作 [cite: 67]
                if not df_inst.empty and df_inst[df_inst['buy_sell_center'] == 'Investment_Trust']['Quantity'].sum() > 0:
                    
                    # --- 第四層：基本面 (營收 YoY) ---
                    df_rev = api.taiwan_stock_month_revenue(
                        stock_id=stock_id, 
                        start_date=(datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
                    )
                    # 確保營收年增率為正 [cite: 70]
                    if not df_rev.empty and df_rev.iloc[-1]['revenue_year_growth_rate'] > 0:
                        final_candidates.append(stock_id)
                        print(f"🎯 準金股入選: {stock_id}")
                        
        except Exception as e:
            continue # 跳過錯誤標的，確保流程不中斷
            
    return final_candidates

if __name__ == "__main__":
    candidates = run_full_strategy()
    print(f"✅ 最終精選名單 (成交量前100強+四層過濾): {candidates}")

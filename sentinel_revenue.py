import os
import json
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
from FinMind.data import DataLoader
from datetime import datetime, timedelta, timezone

# 1. 輔助函式：取得台灣時間
def get_taiwan_time():
    return datetime.now(timezone.utc) + timedelta(hours=8)

# 2. 定義 Firebase 上傳功能 (機器人一號路徑)
def upload_to_firebase(candidates):
    fb_config = os.environ.get('FIREBASE_CONFIG')
    if not fb_config:
        print("❌ 錯誤：GitHub Secrets 中找不到 'FIREBASE_CONFIG'")
        return

    try:
        cred_json = json.loads(fb_config)
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_json)
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'
            })
        
        # 機器人一號專屬節點: sentinel
        ref = db.reference('stock_alerts/sentinel')
        ref.set({
            'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': candidates,
            'strategy_name': 'The Sentinel (營收雙增)',
            'status': 'Success'
        })
        print(f"📢 Sentinel 同步成功！名單：{candidates}")
    except Exception as e:
        print(f"❌ Firebase 處理異常: {e}")

# 3. 定義機器人一號策略：YoY > 20% 且 MoM > 0
def run_sentinel_strategy():
    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN')
    if token: api.login_by_token(token)
    
    tw_now = get_taiwan_time()
    start_date = (tw_now - timedelta(days=90)).strftime("%Y-%m-%d")
    
    # 你的 100 檔熱門清單 (先放指標股測試，確認成功後再加滿)
    raw_list = ['2330', '2317', '2454', '2303', '3481', '2409', '2618', '2344']
    
    final_candidates = []
    print(f"--- 🛰️ The Sentinel 啟動 (營收雙增監控) ---")

    for stock_id in raw_list:
        try:
            # 獲取營收資料
            df_rev = api.taiwan_stock_month_revenue(stock_id=stock_id, start_date=start_date)
            
            if df_rev.empty or len(df_rev) < 1: continue
            
            latest = df_rev.iloc[-1]
            yoy = latest['revenue_year_growth_rate']
            mom = latest['revenue_month_growth_rate']
            
            # 邏輯判斷: YoY > 20 且 MoM > 0
            if yoy > 20 and mom > 0:
                print(f"🎯 {stock_id}: ✅ 符合 (YoY: {yoy}%, MoM: {mom}%)")
                final_candidates.append(stock_id)
        except:
            continue
            
    return final_candidates

# 4. 主程式執行
if __name__ == "__main__":
    result = run_sentinel_strategy()
    print(f"✅ 最終精選名單: {result}")
    upload_to_firebase(result)

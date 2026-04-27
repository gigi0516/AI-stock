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

# 2. 定義 Firebase 上傳功能
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
        
        ref = db.reference('stock_alerts/trend_master')
        ref.set({
            'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': candidates,
            'status': 'Success'
        })
        print(f"📢 Firebase 同步成功！名單：{candidates}")
    except Exception as e:
        print(f"❌ Firebase 處理異常: {e}")

# 3. 定義核心篩選策略
def run_full_strategy():
    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN')
    if token: api.login_by_token(token)
    
    tw_now = get_taiwan_time()
    start_date = (tw_now - timedelta(days=70)).strftime("%Y-%m-%d")
    
    # 測試用名單
    raw_list = ['2330', '2317', '2454', '2303', '2618']
    final_candidates = []

    print(f"--- 🕵️ 開始偵錯掃描 (台灣時間: {tw_now.strftime('%Y-%m-%d')}) ---")
    for stock_id in raw_list:
        try:
            df = api.taiwan_stock_daily(stock_id=stock_id, start_date=start_date)
            if df.empty: continue
            
            # 極度放寬條件以利測試
            latest = df.iloc[-1]
            if latest['close'] > 10:
                print(f"🔍 {stock_id}: ✅ 符合 (股價 {latest['close']})")
                final_candidates.append(stock_id)
        except:
            continue
    return final_candidates

# 4. 這裡才是主程式執行區，必須放在最後面
if __name__ == "__main__":
    # 先跑策略，取得名單
    result = run_full_strategy()
    
    # 再印出名單
    print(f"✅ 最終精選名單: {result}")
    
    # 最後上傳 Firebase
    upload_to_firebase(result)

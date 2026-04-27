import os
import json
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
from FinMind.data import DataLoader
from datetime import datetime, timedelta, timezone

def get_taiwan_time():
    return datetime.now(timezone.utc) + timedelta(hours=8)

def upload_to_firebase(candidates):
    fb_config = os.environ.get('FIREBASE_CONFIG')
    if not fb_config: 
        print("❌ 找不到 FIREBASE_CONFIG Secret")
        return
    try:
        cred_json = json.loads(fb_config)
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_json)
            firebase_admin.initialize_app(cred, {
                'databaseURL': f"https://{cred_json['project_id']}-default-rtdb.firebaseio.com/"
            })
        ref = db.reference('stock_alerts/trend_master')
        ref.set({
            'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': candidates,
            'status': 'Success'
        })
        print(f"📢 Firebase 同步成功！名單：{candidates}")
    except Exception as e:
        print(f"❌ Firebase 錯誤: {e}")

def run_full_strategy():
    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN')
    if token: api.login_by_token(token)
    
    tw_now = get_taiwan_time()
    start_date = (tw_now - timedelta(days=70)).strftime("%Y-%m-%d")
    
    # 縮短清單先測試這 5 檔最熱門的
    raw_list = ['2330', '2317', '2454', '2303', '2618']
    final_candidates = []

    print(f"--- 🕵️ 開始偵錯掃描 (台灣時間: {tw_now.strftime('%Y-%m-%d')}) ---")

    for stock_id in raw_list:
        try:
            print(f"🔍 檢查 {stock_id}...", end=" ")
            df = api.taiwan_stock_daily(stock_id=stock_id, start_date=start_date)
            
            if df.empty:
                print("❌ 沒抓到股價資料")
                continue
            
            df['MA20'] = df['close'].rolling(window=20).mean()
            latest = df.iloc[-1]
            
            # --- 極度放寬的測試條件 ---
            # 只要股價大於 10 元就讓它過（確保測試時有名單）
            if latest['close'] > 10: 
                print(f"✅ 符合測試條件 (股價: {latest['close']})")
                final_candidates.append(stock_id)
            else:
                print(f"❌ 股價太低: {latest['close']}")
        except Exception as e:
            print(f"⚠️ 發生錯誤: {e}")
            continue
            
    print(f"--- 🏁 掃描結束 ---")
    return final_candidates

if __name__ == "__main__":
    result = run_full_strategy()
    print(f"✅ 最終精選名單: {result}") # 這行一定會印出來
    upload_to_firebase(result)

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
    if not fb_config: return
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
        print(f"📢 Firebase 同步成功！")
    except Exception as e:
        print(f"❌ Firebase 錯誤: {e}")

def run_full_strategy():
    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN')
    if token: api.login_by_token(token)
    
    tw_now = get_taiwan_time()
    # 擴大範圍到 7 天，確保一定能抓到最近兩個交易日
    start_date = (tw_now - timedelta(days=7)).strftime("%Y-%m-%d")
    
    # 縮短名單先測試這幾檔指標股
    raw_list = ['2330', '2317', '2454', '2303', '3481', '2409', '2618', '2344']
    final_candidates = []

    print(f"--- 🕵️ 數據偵錯模式 (台灣時間: {tw_now.strftime('%Y-%m-%d')}) ---")

    for stock_id in raw_list:
        try:
            # 獲取法人資料
            df = api.taiwan_stock_institutional_investors_buy_sell(stock_id=stock_id, start_date=start_date)
            
            if df.empty:
                print(f"🔍 {stock_id}: ❌ 無資料")
                continue

            # 找出最後一個交易日
            latest_date = df['date'].max()
            df_latest = df[df['date'] == latest_date]
            
            # 計算外資與投信買賣超 (Quantity 可能為 buy 減 sell)
            f_buy = df_latest[df_latest['name'] == 'Foreign_Investor']['buy'].sum()
            f_sell = df_latest[df_latest['name'] == 'Foreign_Investor']['sell'].sum()
            t_buy = df_latest[df_latest['name'] == 'Investment_Trust']['buy'].sum()
            
            f_net = f_buy - f_sell
            
            # 偵錯印出：讓我們看看數字
            print(f"🔍 {stock_id} ({latest_date}): 外資淨買 {f_net}, 投信買 {t_buy}")

            # 只要外資買超過 0 或 投信買超過 0
            if f_net > 0 or t_buy > 0:
                print(f"   ✅ 符合條件！")
                final_candidates.append(stock_id)
            
        except Exception as e:
            print(f"🔍 {stock_id}: ⚠️ 錯誤 {str(e)}")
            continue
            
    return final_candidates

if __name__ == "__main__":
    result = run_full_strategy()
    print(f"✅ 最終精選名單: {result}")
    upload_to_firebase(result)

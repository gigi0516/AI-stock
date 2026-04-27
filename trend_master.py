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
    # 擴大範圍到 10 天，確保跨週末也抓得到資料
    start_date = (tw_now - timedelta(days=10)).strftime("%Y-%m-%d")
    
    # 使用你原本的 100 檔名單 (這裡先列出部分測試)
    raw_list = ['2330', '2317', '2454', '2303', '3481', '2409', '2618', '2344']
    final_candidates = []

    print(f"--- 🕵️ 數據修正模式 (台灣時間: {tw_now.strftime('%Y-%m-%d')}) ---")

    for stock_id in raw_list:
        try:
            # ✅ 修正後的函式名稱
            df = api.taiwan_stock_institutional_investors(
                stock_id=stock_id, 
                start_date=start_date
            )
            
            if df.empty:
                print(f"🔍 {stock_id}: ❌ 無法人資料")
                continue

            # 找出最後一個交易日
            latest_date = df['date'].max()
            df_latest = df[df['date'] == latest_date]
            
            # 計算淨買超 (buy - sell)
            # 這裡計算外資與投信的總和
            foreign = df_latest[df_latest['name'] == 'Foreign_Investor']
            trust = df_latest[df_latest['name'] == 'Investment_Trust']
            
            f_net = foreign['buy'].sum() - foreign['sell'].sum()
            t_net = trust['buy'].sum() - trust['sell'].sum()
            
            print(f"🔍 {stock_id} ({latest_date}): 外資 {f_net} | 投信 {t_net}")

            # 條件：只要外資或投信其中一個是正的 (買超)
            if f_net > 0 or t_net > 0:
                print(f"   ✅ 符合籌碼優選！")
                final_candidates.append(stock_id)
            
        except Exception as e:
            print(f"🔍 {stock_id}: ⚠️ 執行錯誤 {str(e)}")
            continue
            
    return final_candidates

if __name__ == "__main__":
    result = run_full_strategy()
    print(f"✅ 最終精選名單: {result}")
    upload_to_firebase(result)

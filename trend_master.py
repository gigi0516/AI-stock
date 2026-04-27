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
    raw_list = [
        '00981A', '00631L', '009816', '2344', '00992A', '3481', '00632R', '009819', '2409', '00991A',
        '2303', '0050', '00919', '2337', '00400A', '0056', '6770', '2408', '00878', '2317',
        '00940', '2313', '0052', '4958', '1802', '00929', '2887', '2367', '00982A', '2330',
        '1303', '2002', '00937B', '00664R', '3189', '3035', '00988A', '00997A', '2891', '4927',
        '6182', '2883', '00953B', '2356', '1727', '2312', '3260', '2485', '2884', '00918',
        '00712', '2301', '3231', '009820', '2886', '2464', '00994A', '2890', '2324', '2399',
        '1815', '00891', '00679B', '8028', '2885', '2327', '8027', '2449', '8112', '2892',
        '1717', '5483', '5347', '2834', '00881', '2481', '00687B', '00680L', '3711', '6285',
        '2618', '00993A', '4967', '2882', '8046', '3019', '2812', '3105', '1101', '2355',
        '00927', '1326', '00996A', '2610', '5880', '8064', '2388', '2881', '4906', '2454'
    ]]
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

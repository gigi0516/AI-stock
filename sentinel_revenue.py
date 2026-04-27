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
        
        # 🟢 關鍵：這是機器人一號的專屬頻道
       ref = db.reference('stock_alerts/bot_1') # 確保這裡是 bot_1
        ref.set({
            'bot_id': 'ROBOT_01',  # 加上身分證
            'bot_name': '營收雙增哨兵',
            'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': candidates
        })
        print(f"📢 機器人一號已將名單回報至頻道 bot_1")
    except Exception as e:
        print(f"❌ Firebase 錯誤: {e}")

def run_strategy_v1():
    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN')
    if token: api.login_by_token(token)
    
    tw_now = get_taiwan_time()
    start_date = (tw_now - timedelta(days=65)).strftime("%Y-%m-%d")
    
    # 你的 100 檔熱門清單
    raw_list = [
        '2344', '3481', '2409', '2303', '2337', '6770', '2408', '2317', '2313', '4958', 
        '1802', '2367', '2330', '1303', '2002', '3189', '3035', '4927', '6182', '2883', 
        '2356', '1727', '2312', '3260', '2485', '2884', '2301', '3231', '2886', '2464', 
        '2890', '2324', '2399', '8028', '2885', '2327', '8027', '2449', '8112', '2892', 
        '1717', '5483', '5347', '2834', '2481', '3711', '6285', '2618', '4967', '2882', 
        '8046', '3019', '2812', '3105', '1101', '2355', '1326', '2610', '5880', '8064', 
        '2388', '2881', '4906', '2454'
    ]
    
    final_candidates = []
    print(f"--- 🛰️ 機器人一號任務開始 ---")

    for stock_id in raw_list:
        try:
            df_rev = api.taiwan_stock_month_revenue(stock_id=stock_id, start_date=start_date)
            if df_rev.empty: continue
            
            latest = df_rev.iloc[-1]
            # 邏輯：YoY > 20% 且 MoM > 0
            if latest['revenue_year_growth_rate'] > 20 and latest['revenue_month_growth_rate'] > 0:
                print(f"🎯 {stock_id}: 符合雙增條件")
                final_candidates.append(stock_id)
        except:
            continue
    return final_candidates

if __name__ == "__main__":
    result = run_strategy_v1()
    upload_to_firebase(result)
# 4. 主程式執行
if __name__ == "__main__":
    result = run_sentinel_strategy()
    print(f"✅ 最終精選名單: {result}")
    upload_to_firebase(result)

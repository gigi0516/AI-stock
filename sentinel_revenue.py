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
        ref = db.reference('stock_alerts/bot_1')
        ref.set({
            'bot_id': 'BOT_01_SENTINEL',
            'bot_name': '機器人一號：營收雙增監控',
            'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': candidates,
            'criteria': '真正雙增 (本月 > 上月 且 本月 > 去年同月)'
        })
        print(f"🚀 Firebase 同步成功！名單：{candidates}")
    except Exception as e:
        print(f"❌ Firebase 錯誤: {e}")

def run_sentinel_strategy():
    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN')
    if token: api.login_by_token(token)
    
    tw_now = get_taiwan_time()
    # 關鍵：抓 400 天，確保能抓到去年的同一月份
    start_date = (tw_now - timedelta(days=400)).strftime("%Y-%m-%d")
    
    # 你的 56 檔精選個股
    raw_list = [
        '2344', '3481', '2409', '2303', '2337', '6770', '2408', '2317', '2313', '4958', 
        '1802', '2887', '2367', '2330', '1303', '2002', '3189', '3035', '2891', '4927', 
        '6182', '2883', '2356', '1727', '2312', '3260', '2485', '2884', '2301', '3231', 
        '2886', '2464', '2890', '2324', '2399', '1815', '8028', '2885', '2327', '8027', 
        '2449', '8112', '2892', '1717', '5483', '5347', '2834', '2481', '3711', '6285', 
        '2618', '4967', '2882', '8046', '3019', '2812', '3105', '1101', '2355', '1326', 
        '2610', '5880', '8064', '2388', '2881', '4906', '2454'
    ]
    
    final_candidates = []
    print(f"--- 🛰️ 機器人一號：開始精準營收對決 ---")

    for stock_id in raw_list:
        try:
            df = api.taiwan_stock_month_revenue(stock_id=stock_id, start_date=start_date)
            if len(df) < 13: continue # 至少要有一年以上的資料
            
            # 1. 本月 (最新)
            rev_now = df.iloc[-1]['revenue']
            # 2. 上月
            rev_prev = df.iloc[-2]['revenue']
            # 3. 去年同月 (往前數第 12 個月)
            rev_last_year = df.iloc[-13]['revenue']
            
            # 真正的雙增邏輯
            if rev_now > rev_prev and rev_now > rev_last_year:
                yoy = round(((rev_now - rev_last_year) / rev_last_year) * 100, 1)
                print(f"🎯 {stock_id}: ✅ 雙增 (YoY: {yoy}%)")
                final_candidates.append(stock_id)
        except:
            continue
            
    return final_candidates

if __name__ == "__main__":
    result = run_sentinel_strategy()
    upload_to_firebase(result)

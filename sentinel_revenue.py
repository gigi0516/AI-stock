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
        
        # 🔴 這裡是關鍵：強制寫入 bot_1 聊天室路徑
        ref = db.reference('stock_alerts/bot_1')
        ref.set({
            'bot_id': 'BOT_01_SENTINEL',
            'bot_name': '機器人一號：營收雙增監控',
            'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': candidates,
            'report_msg': f"今日掃描完成，符合營收雙增標的共 {len(candidates)} 檔。"
        })
        print(f"🚀 [機器人一號] 資料已成功推送到 Firebase: bot_1 頻道")
    except Exception as e:
        print(f"❌ [機器人一號] Firebase 錯誤: {e}")

def run_sentinel_strategy():
    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN')
    if token: api.login_by_token(token)
    
    tw_now = get_taiwan_time()
    # 營收抓 60 天內資料
    start_date = (tw_now - timedelta(days=60)).strftime("%Y-%m-%d")
    
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

    print(f"--- 🛰️ 機器人一號 (Sentinel) 營收檢查流程開始 ---")

   for stock_id in raw_list:
        try:
            df_rev = api.taiwan_stock_month_revenue(stock_id=stock_id, start_date=start_date)
            if df_rev.empty or len(df_rev) < 2: continue
            
            # 取得最新一筆 (當月) 和 前一筆 (上月)
            latest = df_rev.iloc[-1]
            previous = df_rev.iloc[-2]
            
            # 暴力比大小：
            # 1. 本月營收 > 上月營收 (就是 MoM > 0)
            # 2. 本月營收 > 去年同月營收 (就是 YoY > 0)
            rev_now = latest['revenue']
            rev_last_month = previous['revenue']
            rev_last_year = latest['last_year_revenue']
            
            if rev_now > rev_last_month and rev_now > rev_last_year:
                # 計算一下比例給日誌看
                yoy_val = round(((rev_now - rev_last_year) / rev_last_year) * 100, 2)
                print(f"🎯 {stock_id}: ✅ 確定雙增！(YoY: {yoy_val}%)")
                final_candidates.append(stock_id)
            else:
                print(f"   {stock_id}: 未達標")
                
        except Exception as e:
            print(f"   {stock_id}: 資料異常 {e}")
            continue
            
    return final_candidates

if __name__ == "__main__":
    result = run_sentinel_strategy()
    print(f"✅ 機器人一號結算名單: {result}")
    upload_to_firebase(result)

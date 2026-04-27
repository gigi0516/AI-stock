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
    
    raw_list = ['2330', '2317', '2454', '2303', '3481', '2409', '2618', '2344', '3035', '2337']
    final_candidates = []

    print(f"--- 🛰️ 機器人一號 (Sentinel) 營收檢查流程開始 ---")

    for stock_id in raw_list:
        try:
            df_rev = api.taiwan_stock_month_revenue(stock_id=stock_id, start_date=start_date)
            if df_rev.empty: continue
            
            latest = df_rev.iloc[-1]
            yoy = latest['revenue_year_growth_rate']
            mom = latest['revenue_month_growth_rate']
            
            # 1 號機器人專屬邏輯：YoY > 20% 且 MoM > 0
            if yoy > 20 and mom > 0:
                print(f"📈 {stock_id}: 符合營收雙增 (YoY: {yoy}%, MoM: {mom}%)")
                final_candidates.append(stock_id)
            else:
                # 偵錯用：印出不符合的原因
                print(f"   {stock_id}: 未達標 (YoY: {yoy}%, MoM: {mom}%)")
        except:
            continue
            
    return final_candidates

if __name__ == "__main__":
    result = run_sentinel_strategy()
    print(f"✅ 機器人一號結算名單: {result}")
    upload_to_firebase(result)

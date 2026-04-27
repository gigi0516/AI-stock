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
        
        ref = db.reference('stock_alerts/bot_4')
        ref.set({
            'bot_id': 'BOT_04_TREND',
            'bot_name': '機器人四號：法人動態監控',
            'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': candidates,
            'criteria': '法人買超排行榜前列 (含 ETF)'
        })
        print(f"🚀 [Trend Master] 資料已推送到 bot_4")
    except Exception as e:
        print(f"❌ Firebase 錯誤: {e}")

def run_trend_strategy():
    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN')
    if token: api.login_by_token(token)
    
    tw_now = get_taiwan_time()
    # 抓取最近 3 天的籌碼資料
    start_date = (tw_now - timedelta(days=3)).strftime("%Y-%m-%d")
    
    # --- 你提供的法人買超名單 (含個股、ETF、權證) ---
    raw_list = [
        '00878', '00940', '0056', '2408', '00919', '2337', '00712', '2344', 
        '00929', '2317', '055151', '00680L', '00918', '3481', '00993A', '00713', 
        '6770', '1303', '4927', '6182', '1806', '1326', '00900', '2883', 
        '054694', '00965', '00715L', '057992', '3231', '009813', '057640', '009820', 
        '056119', '057848', '00904', '2867', '2301', '8112', '056932', '00688L', 
        '050191', '00882', '059177', '057988', '08708U', '051340', '058906', '063811', 
        '2886', '2103', '2884', '1905', '057343', '2327', '060620', '049480', '058899', 
        '03719B', '1314', '00939', '00936', '08899U', '00922', '054658', '00665L', 
        '3033', '2897', '00757', '053602', '034451', '00915', '009811', '00642U', '00637L'
    ]
    
    final_candidates = []
    print(f"--- 🛰️ 機器人四號：開始掃描法人買超動向 ---")

    for stock_id in raw_list:
        try:
            # 獲取三大法人買賣超資料
            df = api.taiwan_stock_institutional_investors(stock_id=stock_id, start_date=start_date)
            if df.empty: continue
            
            # 取得最新一天的資料
            latest_data = df.iloc[-3:] # 確保抓到最後的紀錄
            
            # 檢查外資或投信是否有買進 (買進張數 > 0)
            foreign_buy = latest_data[latest_data['name'] == 'Foreign_Investor']['buy'].sum()
            sitc_buy = latest_data[latest_data['name'] == 'Investment_Trust']['buy'].sum()
            
            if foreign_buy > 0 or sitc_buy > 0:
                print(f"✅ {stock_id}: 法人有動作 (外資:{foreign_buy} / 投信:{sitc_buy})")
                final_candidates.append(stock_id)
        except:
            continue
            
    return final_candidates

if __name__ == "__main__":
    result = run_trend_strategy()
    print(f"🏁 最終名單: {result}")
    upload_to_firebase(result)

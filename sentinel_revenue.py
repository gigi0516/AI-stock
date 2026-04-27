import os
import json
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
from FinMind.data import DataLoader
from datetime import datetime, timedelta, timezone

# 1. 取得台灣時間
def get_taiwan_time():
    return datetime.now(timezone.utc) + timedelta(hours=8)

# 2. Firebase 上傳 (路徑設為 sentinel)
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
        
        # 機器人一號的路徑：stock_alerts/sentinel
        ref = db.reference('stock_alerts/sentinel')
        ref.set({
            'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': candidates,
            'strategy_name': 'The Sentinel (營收雙增)',
            'status': 'Success'
        })
        print(f"📢 Sentinel 同步成功！名單：{candidates}")
    except Exception as e:
        print(f"❌ Firebase 錯誤: {e}")

# 3. 核心策略：營收雙增邏輯
def run_sentinel_strategy():
    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN')
    if token: api.login_by_token(token)
    
    tw_now = get_taiwan_time()
    # 抓取近 90 天營收資料，確保能涵蓋最新一期
    start_date = (tw_now - timedelta(days=90)).strftime("%Y-%m-%d")
    
    # 使用你的 100 檔熱門股清單
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
    print(f"--- 🛰️ The Sentinel 啟動 (營收監控模式) ---")

    for stock_id in raw_list:
        try:
            # 獲取營收資料
            df_rev = api.taiwan_stock_month_revenue(stock_id=stock_id, start_date=start_date)
            
            if df_rev.empty or len(df_rev) < 2: continue
            
            # 取得最新一期營收數據
            latest = df_rev.iloc[-1]
            
            # 邏輯判斷：
            # 1. YoY (revenue_year_growth_rate) > 20
            # 2. MoM (revenue_month_growth_rate) > 0
            yoy = latest['revenue_year_growth_rate']
            mom = latest['revenue_month_growth_rate']
            
            if yoy > 20 and mom > 0:
                print(f"🎯 {stock_id}: ✅ 營收爆發 (YoY: {yoy}%, MoM: {mom}%)")
                final_candidates.append(stock_id)
                
        except Exception as e:
            continue
            
    return final_candidates

if __name__ == "__main__":
    candidates = run_sentinel_strategy()
    print(f"✅ Sentinel 精選名單: {candidates}")
    upload_to_firebase(candidates)

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
            'bot_name': '機器人一號：營收成長監控',
            'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': candidates,
            'criteria': '營收金額雙增 (本月 > 上月 且 本月 > 去年同月)'
        })
        print(f"🚀 [機器人一號] 資料已成功推送到 Firebase: bot_1")
    except Exception as e:
        print(f"❌ [機器人一號] Firebase 錯誤: {e}")

def run_sentinel_strategy():
    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN')
    if token: api.login_by_token(token)
    
    tw_now = get_taiwan_time()
    # 稍微拉長天數到 100 天，確保能抓到對照用的營收資料
    start_date = (tw_now - timedelta(days=100)).strftime("%Y-%m-%d")
    
    # 56 檔精選個股名單
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
    print(f"--- 🛰️ 機器人一號：開始營收對決掃描 ---")

    for stock_id in raw_list:
        try:
            df_rev = api.taiwan_stock_month_revenue(stock_id=stock_id, start_date=start_date)
            # 必須至少有兩筆資料才能比對
            if df_rev.empty or len(df_rev) < 2:
                continue
            
            # 取得最近兩筆資料
            latest = df_rev.iloc[-1]
            previous = df_rev.iloc[-2]
            
            # 提取核心營收數字
            rev_now = latest['revenue']           # 本月營收
            rev_prev = previous['revenue']        # 上月營收
            rev_year = latest['last_year_revenue'] # 去年同月營收
            
            # 邏輯：有漲就好 (暴力比大小)
            if rev_now > rev_prev and rev_now > rev_year:
                print(f"🎯 {stock_id}: ✅ 營收向上 (本月:{rev_now} > 上月:{rev_prev})")
                final_candidates.append(stock_id)
            else:
                pass # 不符合就不印，節省日誌空間
                
        except:
            continue
            
    return final_candidates

if __name__ == "__main__":
    result = run_sentinel_strategy()
    print(f"✅ 最終結算名單: {result}")
    upload_to_firebase(result)

import os
import json
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
from FinMind.data import DataLoader
from datetime import datetime, timedelta, timezone

# 1. 輔助函式：取得台灣時間
def get_taiwan_time():
    return datetime.now(timezone.utc) + timedelta(hours=8)

# 2. 定義 Firebase 上傳功能
def upload_to_firebase(candidates):
    fb_config = os.environ.get('FIREBASE_CONFIG')
    if not fb_config:
        print("❌ 錯誤：GitHub Secrets 中找不到 'FIREBASE_CONFIG'")
        return

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
        print(f"📢 Firebase 同步成功！名單：{candidates}")
    except Exception as e:
        print(f"❌ Firebase 處理異常: {e}")

# 3. 定義核心篩選策略
def run_full_strategy():
    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN')
    if token: api.login_by_token(token)
    
    tw_now = get_taiwan_time()
    start_date = (tw_now - timedelta(days=70)).strftime("%Y-%m-%d")
    
    
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
]
    final_candidates = []

    print(f"--- 🕵️ 開始偵錯掃描 (台灣時間: {tw_now.strftime('%Y-%m-%d')}) ---")
    for stock_id in raw_list:
        try:
            df = api.taiwan_stock_daily(stock_id=stock_id, start_date=start_date)
            if df.empty: continue
            
            # 極度放寬條件以利測試
            latest = df.iloc[-1]
     df['MA20'] = df['close'].rolling(window=20).mean()
     if latest['close'] > df['MA20'].iloc[-1]: # 股價在月線之上
         df_inst = api.taiwan_stock_institutional_investors_buy_sell(stock_id=stock_id, start_date=... )
            if df_inst['Quantity'].sum() > 0: # 法人近期合計為買超
                if df_rev.iloc[-1]['revenue_year_growth_rate'] > 0: # 營收年增率為正
                print(f"🔍 {stock_id}: ✅ 符合 (股價 {latest['close']})")
                final_candidates.append(stock_id)
        except:
            continue
    return final_candidates

# 4. 這裡才是主程式執行區，必須放在最後面
if __name__ == "__main__":
    # 先跑策略，取得名單
    result = run_full_strategy()
    
    # 再印出名單
    print(f"✅ 最終精選名單: {result}")
    
    # 最後上傳 Firebase
    upload_to_firebase(result)

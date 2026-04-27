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

def run_full_strategy():
    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN')
    if token: api.login_by_token(token)
    
    tw_now = get_taiwan_time()
    # 這裡稍微拉長一點（5天），確保能抓到「上週四、五」的法人資料
    start_date_inst = (tw_now - timedelta(days=5)).strftime("%Y-%m-%d")
    
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
    print(f"--- 🕵️ 開始「雙日籌碼」篩選 (台灣時間: {tw_now.strftime('%Y-%m-%d')}) ---")

    for stock_id in raw_list:
        try:
            # 1. 抓取籌碼面資料
            df_inst = api.taiwan_stock_institutional_investors_buy_sell(
                stock_id=stock_id, 
                start_date=start_date_inst
            )
            
            if not df_inst.empty:
                # 計算外資與投信近期的買超總和
                foreign_buy = df_inst[df_inst['name'] == 'Foreign_Investor']['Quantity'].sum()
                trust_buy = df_inst[df_inst['name'] == 'Investment_Trust']['Quantity'].sum()
                
                # 只要有一方是正的就過
                if foreign_buy > 0 or trust_buy > 0:
                    # ✅ 關鍵修正：直接加入名單，跳過複雜的 YoY 判斷（因為假日或 API 延遲可能抓不到 YoY）
                    print(f"🎯 {stock_id}: ✅ 符合籌碼 (外:{foreign_buy}/投:{trust_buy})")
                    final_candidates.append(stock_id)
        except Exception as e:
            continue
            
    return final_candidates

if __name__ == "__main__":
    result = run_full_strategy()
    print(f"✅ 最終精選名單: {result}")
    upload_to_firebase(result)

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

def run_full_strategy():
    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN')
    if token: api.login_by_token(token)
    
    tw_now = get_taiwan_time()
    # 設定籌碼觀察期為近 3 天
    start_date_inst = (tw_now - timedelta(days=3)).strftime("%Y-%m-%d")
    
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
    print(f"--- 🕵️ 開始「籌碼優先」篩選 (台灣時間: {tw_now.strftime('%Y-%m-%d')}) ---")

    for stock_id in raw_list:
        try:
            # 1. 抓取籌碼面資料 (外資與投信)
            df_inst = api.taiwan_stock_institutional_investors_buy_sell(
                stock_id=stock_id, 
                start_date=start_date_inst
            )
            
            if not df_inst.empty:
                # 分別計算外資與投信的合計買賣超
                foreign_buy = df_inst[df_inst['name'] == 'Foreign_Investor']['Quantity'].sum()
                trust_buy = df_inst[df_inst['name'] == 'Investment_Trust']['Quantity'].sum()
                
                # 條件：外資 > 0 OR 投信 > 0 (只要一方有買超)
                if foreign_buy > 0 or trust_buy > 0:
                    
                    # 2. 抓取基本面 (營收 YoY)
                    df_rev = api.taiwan_stock_month_revenue(
                        stock_id=stock_id, 
                        start_date=(tw_now - timedelta(days=65)).strftime("%Y-%m-%d")
                    )
                    
                    if not df_rev.empty and df_rev.iloc[-1]['revenue_year_growth_rate'] > 0:
                        # 3. 獲取最新股價 (僅作為顯示資訊)
                        df_price = api.taiwan_stock_daily(stock_id=stock_id, start_date=(tw_now - timedelta(days=5)).strftime("%Y-%m-%d"))
                        latest_price = df_price.iloc[-1]['close'] if not df_price.empty else "N/A"
                        
                        print(f"🎯 {stock_id}: ✅ 法人進場 (外:{foreign_buy}/投:{trust_buy}), 股價 {latest_price}")
                        final_candidates.append(stock_id)
        except:
            continue
            
    return final_candidates
# 4. 主程式執行區
if __name__ == "__main__":
    result = run_full_strategy()
    print(f"✅ 最終精選名單: {result}")
    upload_to_firebase(result)

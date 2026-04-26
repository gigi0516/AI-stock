import os
import json
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
from FinMind.data import DataLoader
from datetime import datetime, timedelta

# --- 第一部分：資料庫同步邏輯 ---
def upload_to_firebase(candidates):
    """將選股結果同步至 Firebase Realtime Database"""
    fb_config = os.environ.get('FIREBASE_CONFIG')
    if not fb_config:
        print("❌ 錯誤：找不到環境變數 FIREBASE_CONFIG")
        return

    try:
        cred_json = json.loads(fb_config)
        cred = credentials.Certificate(cred_json)
        
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {
                'databaseURL': f"https://{cred_json['project_id']}-default-rtdb.firebaseio.com/"
            })
        
        push_data = {
            'last_update': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': candidates,
            'strategy_name': 'The Trend-Master',
            'status': 'Success' if candidates else 'No match today'
        }

        ref = db.reference('stock_alerts/trend_master')
        ref.set(push_data)
        print(f"📢 Firebase 同步成功！傳送標的：{candidates}")

    except Exception as e:
        print(f"❌ Firebase 錯誤: {str(e)}")

# --- 第二部分：核心選股策略 ---
def run_full_strategy():
    """執行四層過濾邏輯"""
    token = os.environ.get('FINMIND_TOKEN')
    api = DataLoader()
    if token: 
        api.login_by_token(token)
    
    # 定義監控名單
    raw_list = [
        '3481', '2409', '2303', '2337', '2344', '1802', '2313', '4958', '2408', 
        '6770', '2367', '2317', '2312', '1717', '3189', '2542', '1303', '2399', 
        '6176', '2388', '2330', '2436', '2356', '2002', '3231', '1309', '2485', 
        '8150', '2449', '2324', '4927', '2327', '2316', '2355', '6285', '3711', 
        '2464', '1301', '2301', '2353', '2618', '3019', '3338', '3045'
    ]
    
    print(f"🚀 啟動全能趨勢過濾機器人 (掃描標的: {len(raw_list)} 檔)...")
    final_candidates = []

    for stock_id in raw_list:
        try:
            # 第一、二層：技術面與成交量
            df_price = api.taiwan_stock_daily(stock_id=stock_id, start_date=(datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d"))
            if len(df_price) < 20: continue
            
            df_price['MA20'] = df_price['close'].rolling(window=20).mean()
            latest = df_price.iloc[-1]
            
            # 條件 1：股價 P > MA20
            if latest['close'] > latest['MA20']:
                # 第三層：籌碼面 (近5日法人買超合計 > 0)
                df_inst = api.taiwan_stock_institutional_investors_buy_sell(
                    stock_id=stock_id, 
                    start_date=(datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
                )
                if df_inst['Quantity'].sum() > 0:
                    # 第四層：基本面 (最新營收 YoY > 0)
                    df_rev = api.taiwan_stock_month_revenue(
                        stock_id=stock_id, 
                        start_date=(datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
                    )
                    if not df_rev.empty and df_rev.iloc[-1]['revenue_year_growth_rate'] > 0:
                        final_candidates.append(stock_id)
                        print(f"🎯 符合標的: {stock_id}")
        except:
            continue
            
    return final_candidates

# --- 第三部分：主執行程序 ---
if __name__ == "__main__":
    # 1. 執行策略
    result_list = run_full_strategy()
    
    # 2. 印出結果
    print(f"✅ 最終精選名單: {result_list}")
    
    # 3. 同步至 Firebase
    upload_to_firebase(result_list)

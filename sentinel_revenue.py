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
            'bot_id': 'BOT_01_DEBUG',
            'bot_name': '機器人一號：數據偵錯模式',
            'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': candidates
        })
        print(f"🚀 Firebase 同步完成")
    except Exception as e:
        print(f"❌ Firebase 錯誤: {e}")

def run_sentinel_strategy():
    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN')
    if token: api.login_by_token(token)
    
    tw_now = get_taiwan_time()
    # 擴大範圍到 120 天，確保能看到 1、2、3 月的資料
    start_date = (tw_now - timedelta(days=120)).strftime("%Y-%m-%d")
    
    raw_list = ['2344', '2330', '2454', '2317', '2618'] # 先拿這幾檔指標測試
    final_candidates = []

    print(f"--- 🛰️ 機器人一號：數據偵錯模式啟動 ---")

    for stock_id in raw_list:
        try:
            df_rev = api.taiwan_stock_month_revenue(stock_id=stock_id, start_date=start_date)
            
            if df_rev.empty:
                print(f"⚠️ {stock_id}: 找不到任何營收資料")
                continue

            # ---------------------------------------------------------
            # 🕵️ 關鍵偵錯：印出第一檔股票的所有欄位和最後兩筆資料
            if stock_id == '2344':
                print(f"📊 [偵錯報告] 2344 數據欄位: {df_rev.columns.tolist()}")
                print(f"📊 [偵錯報告] 最新一筆資料內容:\n{df_rev.iloc[-1].to_dict()}")
            # ---------------------------------------------------------

            latest = df_rev.iloc[-1]
            previous = df_rev.iloc[-2]
            
            # 使用更穩定的欄位名稱索引
            rev_now = latest.get('revenue', 0)
            rev_prev = previous.get('revenue', 0)
            # 有些 API 版本欄位叫 'last_year_revenue'，有些叫 'last_year_rev'
            rev_year = latest.get('last_year_revenue', 0)

            if rev_now > rev_prev and rev_now > rev_year:
                print(f"🎯 {stock_id}: ✅ 發現成長 (今:{rev_now} / 昨:{rev_prev} / 去年:{rev_year})")
                final_candidates.append(stock_id)
            
        except Exception as e:
            print(f"❌ {stock_id} 處理出錯: {e}")
            continue
            
    return final_candidates

if __name__ == "__main__":
    result = run_sentinel_strategy()
    print(f"✅ 最終結果: {result}")
    upload_to_firebase(result)

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
    if not firebase_admin._apps:
        cred = credentials.Certificate(json.loads(fb_config))
        firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})
    
    ref = db.reference('stock_alerts/bot_1')
    ref.set({
        'bot_name': '機器人一號：長線營收王',
        'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
        'candidates': candidates if candidates else ["目前尚無連續 4 月雙增標的"],
        'criteria': '長線趨勢：連續 4 個月營收雙增 (YoY & MoM > 1%)'
    })

    print("--- 🚀 機器人一號：長線營收趨勢掃描啟動 ---")
    
    token = os.environ.get('FINMIND_TOKEN', '')
    dl = DataLoader()
    dl.login_token(token)

    # 1. 取得台股所有編號 (此處以你關注的清單或全市場為例)
    # 為了示範，我們先用一小組清單，如果你要全市場，需先抓取股票列表
    target_stocks = ["2330", "2317", "2454", "2308", "2382", "3034"] 
    
    final_candidates = []

    for stock_id in target_stocks:
        try:
            # 抓取過去 15 個月的營收 (確保有足夠數據算 YoY 和 連續性)
            df = dl.taiwan_stock_month_revenue(
                stock_id=stock_id,
                start_date=(tw_now - timedelta(days=500)).strftime("%Y-%m-%d")
            )
            
            if len(df) < 15: continue

            # 轉成 numeric 確保計算正確
            df['revenue'] = pd.to_numeric(df['revenue'])
            
            # --- 連續 4 個月雙增判斷邏輯 ---
            success_months = 0
            # 從最新的月份往回推算 4 個月
            for i in range(1, 5):
                idx = -i
                rev_now = df.iloc[idx]['revenue']
                rev_prev = df.iloc[idx-1]['revenue'] # 上個月
                rev_last_year = df.iloc[idx-12]['revenue'] # 去年同月
                
                # 判定當月是否雙增 > 1%
                is_growing = (rev_now > rev_prev * 1.01) and (rev_now > rev_last_year * 1.01)
                
                if is_growing:
                    success_months += 1
                else:
                    break # 只要一個月沒達標，就不用再往回看了
            
            if success_months >= 4:
                stock_name = df.iloc[-1].get('stock_name', stock_id)
                final_candidates.append(f"{stock_id} {stock_name}")
                print(f"✅ 發現標的: {stock_id} 連續 {success_months} 個月雙增")

        except Exception as e:
            print(f"❌ 處理 {stock_id} 時出錯: {e}")
            continue

    # 2. 同步結果
    upload_to_firebase(final_candidates)

if __name__ == "__main__":
    run_sentinel_strategy()

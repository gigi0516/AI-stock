import os
import json
import firebase_admin
from firebase_admin import credentials, db
from FinMind.data import DataLoader
from datetime import datetime, timedelta, timezone

def run_sentinel_strategy():
    tw_now = get_taiwan_time()
    print(f"--- 🚀 機器人一號：持股營收哨兵啟動 ({tw_now.strftime('%Y-%m-%d %H:%M:%S')}) ---")

    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN', '')
    
    # --- 重要：先在外面登入一次 ---
    if token:
        api.login_by_token(api_token=token)
    # --------------------------

    my_stocks = ["2330", "2337", "2454", "2308", "2317", "7794", "2072"]
    start_date = (tw_now - timedelta(days=180)).strftime("%Y-%m-%d")
    qualified_candidates = []
    
    for stock_id in my_stocks:
        # 3. Firebase 寫入
    try:
        fb_config = os.environ.get('FIREBASE_CONFIG')
        if fb_config and not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(fb_config))
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})

        if firebase_admin._apps:
            db.reference('stock_alerts/bot_1').set({
                'bot_name': '🚀 機器人一號：持股營收哨兵',
                'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
                'candidates': qualified_candidates if qualified_candidates else ["監控標的暫無雙增"],
                'criteria': '監控持股：連續 4 月營收年增 > 1%'
            })
            print(f"🏁 Firebase 資料寫入成功")
    except Exception as fb_e:
        # 確保這裡只有這行，沒有任何 *** 或多餘字元
        print(f"❌ Firebase 錯誤: {fb_e}")

    print(f"🏁 一號機執行完畢")

if __name__ == "__main__":
    run_sentinel_strategy()

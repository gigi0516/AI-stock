import os
import json
import pandas as pd
import firebase_admin
from firebase_admin import credentials, db
from FinMind.data import DataLoader
from datetime import datetime, timedelta, timezone

def run_bot_2_strategy():
    # --- 新增這段判斷 ---
    tw_now = get_taiwan_time()
    today_str = tw_now.strftime("%Y-%m-%d")
    
    # 週末直接收工 (雖然 YAML 過濾了，但 Python 雙重保險更好)
    if tw_now.weekday() >= 5:
        print("☕ 週末休市中，不執行。")
        return

    # 抓取資料後判斷是否為空
    url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
    response = requests.get(url, timeout=30)
    data = response.json()

    if not data or len(data) == 0:
        print(f"😴 今天 ({today_str}) 台股休市或尚未產出資料，機器人先去休息囉！")
        return
  
        
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
            'bot_name': '機器人一號：營收雙增監控',
            'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': candidates,
            'criteria': '真正雙增 (本月 > 上月 且 本月 > 去年同月)'
        })
        print(f"🚀 Firebase 同步成功！名單：{candidates}")
    except Exception as e:
        print(f"❌ Firebase 錯誤: {e}")

def run_long_term_revenue_strategy():
    # 這裡我們需要 Firebase 幫我們記住『連續次數』
    print("--- 🚀 機器人一號：長線營收趨勢掃描 (連續 4 月雙增) ---")
    
    # 取得最新營收資料 (以 FinMind 或其他 API)
    # 假設我們拿到一個 stock_id 的營收清單
    
    # 計算最新月份的 MoM 與 YoY
    rev_now = df.iloc[-1]['revenue']
    rev_prev = df.iloc[-2]['revenue']
    rev_last_year = df.iloc[-13]['revenue']
    
    is_growing = (rev_now > rev_prev * 1.01) and (rev_now > rev_last_year * 1.01)
    
    # 從 Firebase 讀取該股票之前的『連續計數』
    count_ref = db.reference(f'bot_1_counts/{stock_id}')
    current_count = count_ref.get() or 0
    
    if is_growing:
        new_count = current_count + 1
    else:
        new_count = 0 # 只要一個月沒達標，計數就歸零重來
        
    # 更新計數回 Firebase
    count_ref.set(new_count)
    
    # 判斷是否達標 (連續 4 個月)
    if new_count >= 4:
        return True # 進入最終名單

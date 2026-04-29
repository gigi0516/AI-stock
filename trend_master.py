import requests
import os
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta, timezone

def get_taiwan_time():
    # 強制取得台灣時間 (UTC+8)
    return datetime.now(timezone.utc) + timedelta(hours=8)

def run_bot_4_strategy():
    tw_now = get_taiwan_time()
    today_str = tw_now.strftime("%Y-%m-%d")
    
    # 1. 週末判斷
    if tw_now.weekday() >= 5:
        print("☕ 週末休市中，四號機器人休息。")
        return

    print(f"--- 🚀 機器人四號：開始全市場法人淨買超掃描 ({today_str}) ---")
    
    # 2. 加上 Headers 避免被阻擋
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # 三大法人買賣超日報 (T86W0)
    url = "https://openapi.twse.com.tw/v1/fund/T86W0"
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        # 3. 休市攔截：檢查狀態碼與內容
        if response.status_code != 200 or not response.text.strip():
            print(f"😴 今天 ({today_str}) 證交所未提供法人資料，可能是休市。")
            return

        data = response.json()
        
        # 如果回傳是空的陣列，也代表沒開盤
        if not data or len(data) == 0:
            print(f"😴 證交所資料為空，今日 ({today_str}) 應為休市。")
            return

        # 4. 篩選今日法人買超名單 (外資+投信 > 0)
        today_net_buy_list = []
        for item in data:
            try:
                # 取得外資與投信買賣超張數
                foreign = int(item.get('ForeignInvestorsBuySellDiff', '0').replace(',', ''))
                sitc = int(item.get('InvestmentTrustBuySellDiff', '0').replace(',', ''))
                
                if (foreign + sitc) > 0:
                    today_net_buy_list.append(item.get('Code'))
            except:
                continue

        print(f"✅ 今日法人有買進標的共 {len(today_net_buy_list)} 檔")

        # 5. Firebase 初始化 (如果尚未初始化)
        fb_config = os.environ.get('FIREBASE_CONFIG')
        if not fb_config: return
        
        if not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(fb_config))
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})

        # 6. 呼叫連續買超檢查邏輯
        # (這裡假設你原本就有 update_and_check_continuous 這個函數)
        update_and_check_continuous(today_net_buy_list)

    except Exception as e:
        print(f"❌ 四號機器人發生錯誤: {e}")

# --- 下面放你的 update_and_check_continuous 函數內容 ---
def update_and_check_continuous(today_list):
    # 這裡放你原本四號機器人比對連續 3 日買超的邏輯...
    pass

if __name__ == "__main__":
    run_bot_4_strategy()

import requests
import os
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta, timezone

def get_taiwan_time():
    return datetime.now(timezone.utc) + timedelta(hours=8)

def run_bot_4_strategy():
    tw_now = get_taiwan_time()
    today_str = tw_now.strftime("%Y-%m-%d")
    
    if tw_now.weekday() >= 5:
        print(f"☕ 週末休市。")
        return

    print(f"--- 🚀 機器人四號：法人淨買超掃描啟動 ({today_str}) ---")
    
    # [關鍵修正 1]：在進入任何邏輯前先定義 data，防止 NameError
    data = [] 
    
    url = "https://openapi.twse.com.tw/v1/fund/T86W0"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        # [關鍵修正 2]：嚴格檢查回傳內容
        if response.status_code == 200 and response.text.strip():
            try:
                data = response.json()
            except:
                print("❌ 證交所回傳非 JSON 格式，跳過處理。")
                data = [] # 確保後續迴圈不報錯
        else:
            print(f"😴 今日資料未更新或請求失敗 (Status: {response.status_code})")
            data = []

        # 現在即使 data 為空列表，執行此行也不會報 NameError
        today_net_buy_list = []
        for item in data:
            try:
                # 相容中文與英文 Key
                code = item.get('Code', item.get('證券代號', '')).strip()
                if not code: continue

                # 抓取外資與投信買賣超
                f_buy = str(item.get('ForeignInvestorsBuySellDiff', item.get('外資買賣超股數', '0'))).replace(',', '')
                i_buy = str(item.get('InvestmentTrustBuySellDiff', item.get('投信買賣超股數', '0'))).replace(',', '')

                if (int(f_buy) + int(i_buy)) > 0:
                    today_net_buy_list.append(code)
            except:
                continue

        # 3. Firebase 初始化
        fb_config_str = os.environ.get('FIREBASE_CONFIG')
        if fb_config_str and not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(fb_config_str))
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})

        if firebase_admin._apps:
            # 寫入 App 顯示區
            db.reference('stock_alerts/bot_4').set({
                'bot_name': '🚀 機器人四號：法人連買王',
                'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
                'candidates': today_net_buy_list if today_net_buy_list else ["今日尚未發現法人合買標的"],
                'criteria': '籌碼面：外資與投信當日合力買超'
            })
            print(f"✅ 掃描完成，今日標的共 {len(today_net_buy_list)} 檔")

    except Exception as e:
        print(f"❌ 四號機器人發生嚴重故障：{e}")

if __name__ == "__main__":
    run_bot_4_strategy()

if __name__ == "__main__":
    run_bot_4_strategy()

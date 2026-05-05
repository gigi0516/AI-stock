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
        print(f"☕ 週末休市，不執行掃描。")
        return

    print(f"--- 🚀 機器人四號：法人淨買超掃描啟動 ({today_str}) ---")
    
    url = "https://openapi.twse.com.tw/v1/fund/T86W0"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    # [關鍵修正]：先初始化 data 為空列表，防止 NameError
    data = [] 

    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200 and response.text.strip():
            try:
                data = response.json()
            except Exception:
                print("❌ 證交所回傳非 JSON 格式。")
                return
        else:
            print(f"😴 今日 ({today_str}) 證交所資料未更新。")
            return

        if not data:
            return

        today_net_buy_list = []
        
        # 現在執行 for item in data 就不會報 NameError 了
        for item in data:
            try:
                # 偵測代碼：相容 'Code' 或 '證券代號'
                code = item.get('Code', item.get('證券代號', '')).strip()
                if not code: continue

                # 偵測法人買賣超欄位 (相容英/中 Key)
                f_buy_str = item.get('ForeignInvestorsBuySellDiff', item.get('外資買賣超股數', '0'))
                i_buy_str = item.get('InvestmentTrustBuySellDiff', item.get('投信買賣超股數', '0'))

                f_buy = int(str(f_buy_str).replace(',', ''))
                i_buy = int(str(i_buy_str).replace(',', ''))
                
                if (f_buy + i_buy) > 0:
                    today_net_buy_list.append(code)
            except:
                continue

        # Firebase 更新邏輯 (請確保與你的 App 同步)
        fb_config_str = os.environ.get('FIREBASE_CONFIG')
        if fb_config_str and not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(fb_config_str))
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})

        if firebase_admin._apps:
            # 這裡執行你原本的 update_and_check_continuous 或是直接寫入 Firebase
            db.reference('stock_alerts/bot_4').set({
                'bot_name': '🚀 機器人四號：法人連買王',
                'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
                'candidates': today_net_buy_list if today_net_buy_list else ["今日法人未同步買進標的"],
                'criteria': '籌碼面：外資與投信當日合力買超'
            })
            print(f"✅ 掃描完成，今日法人買進 {len(today_net_buy_list)} 檔")

    except Exception as e:
        print(f"❌ 四號機器人執行失敗: {e}")

if __name__ == "__main__":
    run_bot_4_strategy()

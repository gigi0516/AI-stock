from FinMind.data import DataLoader
import os
import json
import firebase_admin
from firebase_admin import credentials, db

def run_bot_4_finmind():
    # 1. 初始化 FinMind (如果有 Token 就填入，沒有則使用有限制的免費版)
    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN', '')
    if token: api.login_token(token)

    # 2. 指定你想觀察的重點標的 (例如你的持股 0050, 2330 等)
    stock_list = ["2330", "2317", "2454", "2308", "2382"] 
    qualified = []

    for code in stock_list:
        try:
            # 抓取三大法人買賣超資料
            df = api.taiwan_stock_holding_shares_per(
                stock_id=code,
                start_date='2026-05-01' # 根據當前時間調整
            )
            
            if not df.empty and len(df) >= 3:
                # 檢查最近三天投信或外資是否持續買進
                recent = df.tail(3)
                # 這裡可以根據你的邏輯定義「好」的標準
                if (recent['Foreign_Investors_Buy'].iloc[-1] > 0):
                    qualified.append(code)
        except:
            continue

    # 3. 推送到 Firebase (路徑與你的 Android App 對接)
    update_firebase('bot_4', qualified, "法人觀測名單")

def update_firebase(bot_id, candidates, name):
    fb_config = os.environ.get('FIREBASE_CONFIG')
    if not fb_config: return
    if not firebase_admin._apps:
        cred = credentials.Certificate(json.loads(fb_config))
        firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})
    
    db.reference(f'stock_alerts/{bot_id}').set({
        'bot_name': name,
        'candidates': candidates if candidates else ["觀察標的暫無變動"],
        'last_update': "2026-05-05 20:15:00" # 範例時間
    })

if __name__ == "__main__":
    run_bot_4_finmind()

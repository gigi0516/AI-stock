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

    # 核心篩選段落
for item in data:
    try:
        # 自動識別股票代碼 (Code 或 證券代號)
        code = item.get('Code', item.get('證券代號', '')).strip()
        if not code: continue

        # [關鍵] 雙重檢查外資與投信欄位
        f_buy = item.get('ForeignInvestorsBuySellDiff', item.get('外資買賣超股數', '0'))
        i_buy = item.get('InvestmentTrustBuySellDiff', item.get('投信買賣超股數', '0'))

        # 轉換數值並過濾
        net_buy = int(str(f_buy).replace(',', '')) + int(str(i_buy).replace(',', ''))
        
        if net_buy > 0:
            today_net_buy_list.append(code)
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

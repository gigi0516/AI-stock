import os
import json
import firebase_admin
from firebase_admin import credentials, db
from FinMind.data import DataLoader
from datetime import datetime, timedelta, timezone

def get_taiwan_time():
    # 強制取得台灣時間 (UTC+8)
    return datetime.now(timezone.utc) + timedelta(hours=8)

def run_bot_4_strategy():
    tw_now = get_taiwan_time()
    today_str = tw_now.strftime("%Y-%m-%d")
    print(f"--- 🚀 機器人四號：FinMind 法人籌碼掃描啟動 ({today_str}) ---")

    # 1. 初始化 FinMind (直接讀取 GitHub Secrets 中的 Token)
    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN', '')

    try:
        # 2. 抓取今日全市場三大法人買賣超資料
        # FinMind 只要不指定 stock_id，就會回傳該日期全市場的資料
        df = api.taiwan_stock_holding_shares_per(
            start_date=today_str,
            token=token
        )
        
        if df.empty:
            print(f"😴 FinMind 尚未更新今日 ({today_str}) 的法人資料，可能需等 15:30 後。")
            return

        # 3. 篩選邏輯：外資 (Foreign_Investors_Buy) > 0 且 投信 (Investment_Trust_Buy) > 0
        # 欄位名稱是 FinMind 標準化過的，不會像證交所 OpenAPI 隨意變動
        qualified = df[
            (df['Foreign_Investors_Buy'] > 0) & 
            (df['Investment_Trust_Buy'] > 0)
        ]
        
        # 取得符合條件的股票代碼清單
        today_net_buy_list = qualified['stock_id'].tolist()
        
        print(f"✅ 成功提取法人同步買進標的，共 {len(today_net_buy_list)} 檔")

        # 4. Firebase 初始化與寫入
        fb_config_str = os.environ.get('FIREBASE_CONFIG')
        if fb_config_str and not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(fb_config_str))
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})

        if firebase_admin._apps:
            db.reference('stock_alerts/bot_4').set({
                'bot_name': '🚀 機器人四號：法人連買王',
                'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
                'candidates': today_net_buy_list if today_net_buy_list else ["今日法人尚未同步買進"],
                'criteria': '籌碼面：外資與投信當日合力買超 (FinMind 穩定版)'
            })
            print(f"🏁 四號機 Firebase 更新完畢")

    except Exception as e:
        print(f"❌ 四號機 (FinMind 版) 執行失敗: {e}")

if __name__ == "__main__":
    run_bot_4_strategy()

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
    print(f"--- 🚀 機器人四號：市值百強全量測試啟動 ({today_str}) ---")

    # 1. 初始化 Firebase
    fb_config_str = os.environ.get('FIREBASE_CONFIG')
    if fb_config_str and not firebase_admin._apps:
        try:
            cred = credentials.Certificate(json.loads(fb_config_str))
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})
        except Exception as e:
            print(f"❌ Firebase 初始化失敗: {e}")
            return

    # 2. 定義完整的市值百強名單
    # 這份名單會直接作為最終結果發送
    top_100_all = [
        "2330", "2308", "2454", "2317", "3711", "0050", "2383", "3037", "2345", "2881",
        "2382", "2882", "2412", "2891", "3017", "2303", "7769", "2360", "6669", "2408",
        "2368", "1303", "2885", "2327", "3653", "5274", "3443", "8046", "0056", "2887",
        "2886", "3665", "6505", "2884", "00878", "6223", "8299", "2880", "00919", "3231",
        "2603", "2344", "2890", "2357", "2449", "3045", "2892", "4958", "006208", "2301",
        "2059", "1216", "2883", "6515", "5880", "6274", "4904", "2395", "3008", "3661",
        "3529", "2313", "1301", "6488", "2337", "1326", "2002", "1590", "5347", "1519",
        "3533", "3189", "2379", "2207", "3036", "3081", "3034", "3044", "6446", "2801",
        "3105", "6770", "2912", "4938", "3481", "2615", "1802", "3293", "5871", "6789",
        "2376", "5876", "2404", "2618", "1101", "2609"
    ]

    # 3. 強制寫入 Firebase
    try:
        if firebase_admin._apps:
            db.reference('stock_alerts/bot_4').set({
                'bot_name': '🚀 四號機：百強全量測試',
                'last_update': tw_now.strftime("%Y-%m-%d %H:%M:%S"),
                'candidates': top_100_all, # 直接推送 100 檔
                'criteria': '測試模式：無視條件，直接顯示市值百強名單'
            })
            print(f"✅ 成功推送 {len(top_100_all)} 檔標的至 Firebase。")
            print("請檢查手機 App 是否已顯示完整名單。")
    except Exception as e:
        print(f"❌ 寫入 Firebase 時出錯: {e}")

if __name__ == "__main__":
    run_bot_4_strategy()

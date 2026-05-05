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

    
        
        # 為了避免免費版 API 次數瞬間用完，我們優先檢查你持股或熱門股
        # 或者你可以設定只跑前 500 檔市值較大的
        top_100_stocks = [
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
        for stock_id in top_100_stocks:
    try:
        # 使用 FinMind 抓取該個股今日法人資料
        df = api.taiwan_stock_holding_shares_per(
            stock_id=stock_id,
            start_date=today_str,
            token=token
        )
        
        if not df.empty:
            # 判斷外資與投信是否同時 > 0
            if df.iloc[-1]['Foreign_Investors_Buy'] > 0 and df.iloc[-1]['Investment_Trust_Buy'] > 0:
                qualified_candidates.append(stock_id)
    except:
        continue
        
        if df.empty:
            print(f"😴 FinMind 尚未更新今日 ({today_str}) 的法人資料，可能需等 15:30 後。")
            return
        
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

import os
import json
import firebase_admin
from firebase_admin import credentials, db
from FinMind.data import DataLoader
from datetime import datetime, timedelta, timezone

def get_taiwan_time():
    return datetime.now(timezone.utc) + timedelta(hours=8)

def run_bot_4_strategy():
    tw_now = get_taiwan_time()
    today_str = tw_now.strftime("%Y-%m-%d")
    print(f"--- 🚀 機器人四號：百強籌碼黃金篩選 ({today_str}) ---")

    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN', '') 

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

    qualified_candidates = []

    try:
        # 抓取今日全市場資料 (我們試著一次拿，如果沒權限再改迴圈)
        for stock_id in top_100_stocks:
            try:
                # 抓取日成交與法人資料
                df_deal = api.taiwan_stock_daily(stock_id=stock_id, start_date=today_str, token=token)
                df_chip = api.taiwan_stock_holding_shares_per(stock_id=stock_id, start_date=today_str, token=token)
                
                if df_deal.empty or df_chip.empty: continue
                
                # 計算籌碼面
                f_buy = df_chip.iloc[-1]['Foreign_Investors_Buy']
                i_buy = df_chip.iloc[-1]['Investment_Trust_Buy']
                total_buy_shares = (f_buy + i_buy) / 1000 # 轉成張數
                
                # 計算價格面
                spread = df_deal.iloc[-1]['Spread']
                
                # --- 黃金篩選條件 ---
                # 1. 今日法人合計買超 > 500 張
                # 2. 今日股價收紅 (漲幅 > 0)
                if total_buy_shares > 500 and spread > 0:
                    qualified_candidates.append(stock_id)
                    print(f"🔥 符合黃金條件：{stock_id} (買超 {int(total_buy_shares)} 張)")
            except:
                continue

        # Firebase 更新
        fb_config_str = os.environ.get('FIREBASE_CONFIG')
        if fb_config_str and not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(fb_config_str))
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})

        if firebase_admin._apps:
            db.reference('stock_alerts/bot_4').set({
                'bot_name': '🚀 四號機：百強籌碼金選',
                'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
                'candidates': qualified_candidates if qualified_candidates else ["今日百強無達標標的"],
                'criteria': '條件：市值百強、法人合計買超 > 500張 且 股價收紅'
            })
            print(f"🏁 篩選完畢，共 {len(qualified_candidates)} 檔")

    except Exception as e:
        print(f"❌ 四號機執行失敗: {e}")

if __name__ == "__main__":
    run_bot_4_strategy()

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
    print(f"--- 🚀 機器人四號：百強連買嚴格版 ({today_str}) ---")

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
    # 抓取最近 7 天資料，確保包含昨日交易日
    start_date = (tw_now - timedelta(days=7)).strftime("%Y-%m-%d")

    try:
        for stock_id in top_100_stocks:
            try:
                # 抓取法人資料與成交資料
                df_chip = api.taiwan_stock_holding_shares_per(stock_id=stock_id, start_date=start_date, token=token)
                df_deal = api.taiwan_stock_daily(stock_id=stock_id, start_date=start_date, token=token)
                
                if df_chip.empty or len(df_chip) < 2 or df_deal.empty:
                    continue
                
                # 排序資料 (最新在最後)
                df_chip = df_chip.sort_values('date')
                df_deal = df_deal.sort_values('date')
                
                # --- 核心嚴格邏輯 ---
                # 1. 計算今日(T)與昨日(T-1)的合計淨買超 (外資+投信)
                today_chip = df_chip.iloc[-1]
                prev_chip = df_chip.iloc[-2]
                
                today_net = today_chip['Foreign_Investors_Buy'] + today_chip['Investment_Trust_Buy']
                prev_net = prev_chip['Foreign_Investors_Buy'] + prev_chip['Investment_Trust_Buy']
                
                # 2. 取得今日價格漲跌
                today_spread = df_deal.iloc[-1]['Spread']
                
                # --- 判斷開關 ---
                # 條件：今日淨買超 > 0 且 昨日淨買超 > 0 且 今日收紅
                if today_net > 0 and prev_net > 0 and today_spread > 0:
                    qualified_candidates.append(stock_id)
                    print(f"💎 連買強勢股：{stock_id}")
                    
            except Exception:
                continue

        # Firebase 更新
        fb_config_str = os.environ.get('FIREBASE_CONFIG')
        if fb_config_str and not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(fb_config_str))
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})

        if firebase_admin._apps:
            db.reference('stock_alerts/bot_4').set({
                'bot_name': '🚀 四號機：百強連買嚴格版',
                'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
                'candidates': qualified_candidates if qualified_candidates else ["今日百強無連續買超標的"],
                'criteria': '條件：市值百強、法人合計連續兩日買超 且 今日收紅'
            })
            print(f"🏁 嚴格篩選完畢，共 {len(qualified_candidates)} 檔達標")

    except Exception as e:
        print(f"❌ 四號機執行失敗: {e}")

if __name__ == "__main__":
    run_bot_4_strategy()

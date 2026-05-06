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
    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN', '') 

    # 市值百強名單
    top_100_stocks = ["2330", "2308", "2454", "2317", "3711", "2383", "3037", "2881", "2382", "2882", "2412", "2891", "3017", "2303", "2360", "6669", "2408", "2368", "2885", "2327", "2887", "2886", "3665", "6505", "2884", "6223", "8299", "2880", "3231", "2603", "2344", "2890", "2357", "2449", "3045", "2892", "4958", "2301", "2059", "1216", "2883", "6515", "5880", "6274", "4904", "2395", "3008", "3661", "3529", "2313", "1301", "6488", "2337", "1326", "2002", "1590", "5347", "1519", "3533", "3189", "2379", "2207", "3036", "3081", "3034", "3044", "6446", "2801", "3105", "6770", "2912", "4938", "3481", "2615", "1802", "3293", "5871", "6789", "2376", "5876", "2404", "2618", "1101", "2609"]

    qualified_candidates = []
    # 抓取最近 7 天，確保能取得至少 2 個交易日
    start_date = (tw_now - timedelta(days=7)).strftime("%Y-%m-%d")

    try:
        for stock_id in top_100_stocks:
            try:
                # 抓取法人資料
                df_chip = api.taiwan_stock_holding_shares_per(stock_id=stock_id, start_date=start_date, token=token)
                if df_chip.empty or len(df_chip) < 2: continue
                
                df_chip = df_chip.sort_values('date')
                
                # 計算 T 與 T-1 合計淨買超 (外資+投信)
                day_T = df_chip.iloc[-1]
                day_T1 = df_chip.iloc[-2]
                
                net_T = day_T['Foreign_Investors_Buy'] + day_T['Investment_Trust_Buy']
                net_T1 = day_T1['Foreign_Investors_Buy'] + day_T1['Investment_Trust_Buy']

                # 條件：今日淨買超 > 0 且 昨日淨買超 > 0
                if net_T > 0 and net_T1 > 0:
                    qualified_candidates.append(stock_id)
            except:
                continue

        # Firebase 初始化與寫入
        fb_config = os.environ.get('FIREBASE_CONFIG')
        if fb_config and not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(fb_config))
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})

        db.reference('stock_alerts/bot_4').set({
            'bot_name': '🚀 四號機：權值連買王',
            'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': qualified_candidates if qualified_candidates else ["今日無連續買超標的"],
            'criteria': '條件：市值百強、法人合計連續兩日買超'
        })
        print(f"🏁 篩選完成，共 {len(qualified_candidates)} 檔達標")

    except Exception as e:
        print(f"❌ 執行失敗: {e}")

if __name__ == "__main__":
    run_bot_4_strategy()

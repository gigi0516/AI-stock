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
    print(f"--- 🚀 機器人四號：法人連買進階過濾啟動 ({today_str}) ---")

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
    # 抓取最近 10 天，確保能取得至少 3 個交易日
    start_date = (tw_now - timedelta(days=10)).strftime("%Y-%m-%d")

    try:
        for stock_id in top_100_stocks:
            try:
                df = api.taiwan_stock_holding_shares_per(
                    stock_id=stock_id,
                    start_date=start_date,
                    token=token
                )
                
                # 必須至少有 3 天的交易資料
                if df.empty or len(df) < 3:
                    continue
                
                # 確保按日期排序 (最新在最後)
                df = df.sort_values('date')
                day_T = df.iloc[-1]   # 今天
                day_T1 = df.iloc[-2]  # 昨天
                day_T2 = df.iloc[-3]  # 前天

                # --- 第一關與踢出機制 ---
                # 今日外資與投信買賣超
                f_buy_T = day_T.get('Foreign_Investors_Buy', 0)
                i_buy_T = day_T.get('Investment_Trust_Buy', 0)
                total_net_T = f_buy_T + i_buy_T

                # 踢出機制：今日合記淨買超必須 > 0
                if total_net_T <= 0:
                    continue
                
                # 第一關：今日外資「或」投信任一買超 > 0
                gate_1 = (f_buy_T > 0) or (i_buy_T > 0)

                # --- 第二關：前兩日也要有買超紀錄 ---
                # 檢查 T-1
                gate_T1 = (day_T1.get('Foreign_Investors_Buy', 0) > 0) or (day_T1.get('Investment_Trust_Buy', 0) > 0)
                # 檢查 T-2
                gate_T2 = (day_T2.get('Foreign_Investors_Buy', 0) > 0) or (day_T2.get('Investment_Trust_Buy', 0) > 0)

                if gate_1 and gate_T1 and gate_T2:
                    qualified_candidates.append(stock_id)
                    print(f"✅ 符合連續買超：{stock_id}")
                    
            except Exception:
                continue

        # 3. Firebase 更新
        fb_config_str = os.environ.get('FIREBASE_CONFIG')
        if fb_config_str and not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(fb_config_str))
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})

        if firebase_admin._apps:
            db.reference('stock_alerts/bot_4').set({
                'bot_name': '🚀 機器人四號：法人連買王 (進階過濾)',
                'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
                'candidates': qualified_candidates if qualified_candidates else ["今日無符合連續買超標的"],
                'criteria': '1.今日外資或投信買超且合計>0 2.連續三天皆有法人買超紀錄'
            })
            print(f"🏁 掃描完畢，符合條件共 {len(qualified_candidates)} 檔")

    except Exception as e:
        print(f"❌ 四號機執行失敗: {e}")

if __name__ == "__main__":
    run_bot_4_strategy()

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
    print(f"--- 🚀 四號機：權值連買王啟動 ({tw_now.strftime('%Y-%m-%d %H:%M:%S')}) ---")
    
    api = DataLoader()
    raw_token = os.environ.get('FINMIND_TOKEN', '')
    token = raw_token.strip().replace("'", "").replace('"', "")
    
    if token:
        api.login_by_token(api_token=token)

    # 市值百強名單
    top_100_stocks = ["2330", "2308", "2454", "2317", "3711", "2383", "3037", "2881", "2382", "2882", "2412", "2891", "3017", "2303", "2360", "6669", "2408", "2368", "2885", "2327", "2887", "2886", "3665", "6505", "2884", "6223", "8299", "2880", "3231", "2603", "2344", "2890", "2357", "2449", "3045", "2892", "4958", "2301", "2059", "1216", "2883", "6515", "5880", "6274", "4904", "2395", "3008", "3661", "3529", "2313", "1301", "6488", "2337", "1326", "2002", "1590", "5347", "1519", "3533", "3189", "2379", "2207", "3036", "3081", "3034", "3044", "6446", "2801", "3105", "6770", "2912", "4938", "3481", "2615", "1802", "3293", "5871", "6789", "2376", "5876", "2404", "2618", "1101", "2609"]

    qualified_candidates = []
    # 抓取最近 10 天確保有足夠交易日
    start_date = (tw_now - timedelta(days=10)).strftime("%Y-%m-%d")

    for stock_id in top_100_stocks:
        try:
            df_chip = api.taiwan_stock_institutional_investors(
                stock_id=stock_id, 
                start_date=start_date
            )
            
            if df_chip is None or df_chip.empty:
                continue
                
            # ✨【修正核心】FinMind 原始資料只有 buy 和 sell，必須手動算出 net_buy (買超 = 買進 - 賣出)
            df_chip['net_buy'] = df_chip['buy'] - df_chip['sell']
            
            # 1. 篩選法人：只要 外資(Foreign_Investor) 和 投信(Investment_Trust)
            # 排除自營商避免避險單干擾
            target = ['Foreign_Investor', 'Investment_Trust']
            df_filter = df_chip[df_chip['name'].isin(target)]
            
            if df_filter.empty:
                continue
            
            # 2. 按日期加總：把同一天的外資跟投信買賣超加起來
            daily_sum = df_filter.groupby('date')['net_buy'].sum().reset_index()
            daily_sum = daily_sum.sort_values('date')
            
            if len(daily_sum) < 2:
                continue
            
            # 3. 取得最後兩天資料
            net_T = daily_sum.iloc[-1]['net_buy']   # 今日合計
            net_T1 = daily_sum.iloc[-2]['net_buy']  # 昨日合計
            
            # 4. 判定：連續兩天合計買超 > 0
            if net_T > 0 and net_T1 > 0:
                name = df_chip.iloc[-1].get('stock_name', stock_id)
                qualified_candidates.append(f"🔥 {stock_id} {name}")
                print(f"✅ {stock_id} 達標 (T:{int(net_T)}, T-1:{int(net_T1)})")

        except Exception as e:
            print(f"⚠️ {stock_id} 處理異常: {e}")
            continue

    # 5. Firebase 寫入
    try:
        fb_config = os.environ.get('FIREBASE_CONFIG')
        if fb_config and not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(fb_config))
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})

        if firebase_admin._apps:
            db.reference('stock_alerts/bot_4').set({
                'bot_name': '🚀 四號機：權值連買王',
                'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
                'candidates': qualified_candidates if qualified_candidates else ["今日無權值連買標的"],
                'criteria': '條件：市值百強、外資+投信合計連續兩日買超'
            })
            print(f"🏁 篩選完成，共 {len(qualified_candidates)} 檔達標並寫入 Firebase")
    except Exception as e:
        print(f"❌ Firebase 寫入失敗: {e}")

if __name__ == "__main__":
    run_bot_4_strategy()
if __name__ == "__main__":
    run_bot_4_strategy()

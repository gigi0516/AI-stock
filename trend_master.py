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
    print(f"--- 🚀 機器人四號：百強籌碼集中過濾 ({today_str}) ---")

    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN', '') 
    
    # --- 測試專用：強行塞入數據 ---
    test_candidates = ["2330", "2317", "2454"] # 測試台積電、鴻海、聯發科

    db.reference('stock_alerts/bot_4').set({
        'bot_name': '🚀 四號機：測試模式',
        'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
        'candidates': test_candidates, # 這裡一定會有資料
        'criteria': '測試模式：強行推送百強指標'
     })
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
    start_date = (tw_now - timedelta(days=10)).strftime("%Y-%m-%d")

    try:
        for stock_id in top_100_stocks:
            try:
                df = api.taiwan_stock_holding_shares_per(
                    stock_id=stock_id,
                    start_date=start_date,
                    token=token
                )
                
                if df.empty or len(df) < 3:
                    continue
                
                df = df.sort_values('date')
                
                # 計算過去三天的法人合計淨買超 (外資+投信)
                # 我們看最後三筆資料
                recent_3 = df.tail(3).copy()
                recent_3['total_net'] = recent_3['Foreign_Investors_Buy'] + recent_3['Investment_Trust_Buy']
                
                today_net = recent_3.iloc[-1]['total_net']
                
                # --- 優化後的鬆綁條件 ---
                # 1. 今日「外資+投信」合計必須是正數 (代表大戶整體在買)
                if today_net <= 0:
                    continue
                
                # 2. 趨勢檢查：過去三天中，至少有兩天法人合計是買超的
                buy_days = len(recent_3[recent_3['total_net'] > 0])
                
                if buy_days >= 2:
                    qualified_candidates.append(stock_id)
                    print(f"✅ 籌碼集中標的：{stock_id}")
                    
            except Exception:
                continue

        # 3. Firebase 更新
        fb_config_str = os.environ.get('FIREBASE_CONFIG')
        if fb_config_str and not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(fb_config_str))
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})

        if firebase_admin._apps:
            db.reference('stock_alerts/bot_4').set({
                'bot_name': '🚀 機器人四號：權值籌碼王',
                'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
                'candidates': qualified_candidates if qualified_candidates else ["今日權值股籌碼較分散"],
                'criteria': '1.今日外資投信合計淨買超 2.過去三天內有兩天以上為淨買超'
            })
            print(f"🏁 掃描完畢，符合條件共 {len(qualified_candidates)} 檔")

    except Exception as e:
        print(f"❌ 四號機執行失敗: {e}")

if __name__ == "__main__":
    run_bot_4_strategy()

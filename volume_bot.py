import os
import json
import firebase_admin
from firebase_admin import credentials, db
from FinMind.data import DataLoader
from datetime import datetime, timedelta, timezone
import time

def get_taiwan_time():
    return datetime.now(timezone.utc) + timedelta(hours=8)

def run_bot_2_strategy():
    tw_now = get_taiwan_time()
    today_str = tw_now.strftime("%Y-%m-%d")
    print(f"--- 🚀 機器人二號：FinMind 免費相容版啟動 ({today_str}) ---")

    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN', '') # 免費版也建議帶入 Token 提高次數限制

    try:
        # 1. 先抓取目前所有股票清單
        stock_info = api.taiwan_stock_info()
        # 過濾出一般的普通股 (通常是代碼 4 碼的)
        target_stocks = stock_info[stock_info['stock_id'].str.len() == 4]['stock_id'].tolist()
        
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

        potential_candidates = []
        start_date = (tw_now - timedelta(days=10)).strftime("%Y-%m-%d")

        print(f"📡 正在掃描 {len(priority_stocks)} 檔標的量能...")

        for stock_id in priority_stocks:
            try:
                # 抓取單一個股日成交
                df = api.taiwan_stock_daily(
                    stock_id=stock_id,
                    start_date=start_date,
                    token=token
                )
                
                if df.empty or len(df) < 2:
                    continue
                
                df = df.sort_values('date', ascending=False)
                today_data = df.iloc[0]
                prev_data = df.iloc[1]

                # 邏輯：今日量 > 2000張 且 為昨日 2 倍 且 收紅
                today_vol = today_data['Trading_Volume'] / 1000
                prev_vol = prev_data['Trading_Volume'] / 1000
                
                if today_vol > 2000 and today_vol > (prev_vol * 2) and today_data['Spread'] > 0:
                    stock_name = today_data.get('stock_name', stock_id)
                    potential_candidates.append(f"{stock_id} {stock_name}")
                    print(f"🔥 發現爆量：{stock_id}")
                
                # 免費版頻率限制保護：每次請求稍微停頓一下
                # time.sleep(0.1) 
            except:
                continue

        # 4. Firebase 更新
        fb_config = os.environ.get('FIREBASE_CONFIG')
        if fb_config and not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(fb_config))
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})

        db.reference('stock_alerts/bot_2').set({
            'bot_name': '🚀 機器人二號：短線量能爆發 (免費版)',
            'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': potential_candidates if potential_candidates else ["今日監控範圍內暫無爆量標的"],
            'criteria': '成交量 > 昨日 2 倍 且 股價收紅'
        })
        print(f"🏁 掃描完成")

    except Exception as e:
        print(f"❌ 二號機執行失敗: {e}")

if __name__ == "__main__":
    run_bot_2_strategy()

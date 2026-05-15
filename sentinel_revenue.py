import os
import json
import firebase_admin
from firebase_admin import credentials, db
from FinMind.data import DataLoader
from datetime import datetime, timedelta, timezone

def get_taiwan_time():
    # 取得台灣時間 (UTC+8)
    return datetime.now(timezone.utc) + timedelta(hours=8)

def run_sentinel_strategy():
    tw_now = get_taiwan_time()
    print(f"--- 🚀 機器人一號：持股營收哨兵啟動 ({tw_now.strftime('%Y-%m-%d %H:%M:%S')}) ---")

    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN', '')

    # 1. 定義監控清單
    my_stocks = ["2330", "2337", "2454", "2308", "2317", "7794", "2072"]
    start_date = (tw_now - timedelta(days=180)).strftime("%Y-%m-%d")
    qualified_candidates = []
    
    # 2. 開始執行篩選
    for stock_id in my_stocks:
        try:
            # 抓取營收資料
            df = api.taiwan_stock_month_revenue(
                stock_id=stock_id,
                start_date=start_date,
                token=token
            )
            
            if df.empty or len(df) < 4:
                print(f"⚠️ {stock_id}：資料不足或為空 (抓到 {len(df)} 筆)")
                continue
            
            # 排序並取最新 4 個月
            df = df.sort_values('date')
            recent_4 = df.tail(4)
            
            # 診斷點：印出年增率數據
            yoy_list = recent_4['revenue_year_growth_percent'].tolist()
            print(f"🔍 檢查 {stock_id} 最近 4 月 YoY: {yoy_list}")

            # 判斷邏輯：連續 4 個月年增率都要 > 1%
            is_qualified = True
            for yoy in yoy_list:
                if yoy < 1:
                    is_qualified = False
                    break
            
            status = "🔥" if is_qualified else "⚪"
            name = df.iloc[-1].get('stock_name', stock_id)
            qualified_candidates.append(f"{status} {stock_id} {name}")
            print(f"{status} {stock_id} 判定完成")

        except Exception as e:
            print(f"❌ {stock_id} 發生錯誤: {e}")

    # 3. Firebase 寫入
    try:
        fb_config = os.environ.get('FIREBASE_CONFIG')
        if fb_config and not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(fb_config))
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})

        if firebase_admin._apps:
            db.reference('stock_alerts/bot_1').set({
                'bot_name': '🚀 機器人一號：持股營收哨兵',
                'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
                'candidates': qualified_candidates if qualified_candidates else ["監控標的暫無雙增"],
                'criteria': '監控持股：連續 4 月營收年增 > 1%'
            })
            print(f"🏁 Firebase 資料寫入成功")
    except Exception as fb_e:
        print(f"❌ Firebase 錯誤: {fb_e}")

    print(f"🏁 一號機執行完畢")

if __name__ == "__main__":
    run_sentinel_strategy()

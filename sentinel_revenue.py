import os
import json
import firebase_admin
from firebase_admin import credentials, db
from FinMind.data import DataLoader
from datetime import datetime, timedelta, timezone

def get_taiwan_time():
    return datetime.now(timezone.utc) + timedelta(hours=8)

def run_sentinel_strategy():
    tw_now = get_taiwan_time()
    print(f"--- 🚀 機器人一號：持股營收哨兵啟動 ({tw_now.strftime('%Y-%m-%d')}) ---")

    api = DataLoader()
    # 這裡直接讀取你剛剛提供的 Token
    token = os.environ.get('FINMIND_TOKEN', '')

    # 設定你的監控清單
    my_stocks = ["2330", "2317", "2454", "0050", "0056"] 
    start_date = (tw_now - timedelta(days=180)).strftime("%Y-%m-%d")
    
    qualified_candidates = []
    
    try:
        for stock_id in my_stocks:
            try:
                # [核心修正]：直接在請求時傳入 token
                df = api.taiwan_stock_month_revenue(
                    stock_id=stock_id,
                    start_date=start_date,
                    token=token
                )
                
                if df.empty or len(df) < 4:
                    continue
                
                df = df.sort_values('date')
                recent_4 = df.tail(4)
                
                # 判斷連續 4 月雙增
                is_qualified = True
                for _, row in recent_4.iterrows():
                    if row.get('revenue_month_growth_percent', 0) < 1 or row.get('revenue_year_growth_percent', 0) < 1:
                        is_qualified = False
                        break
                
                status = "🔥" if is_qualified else "⚪"
                name = df.iloc[-1].get('stock_name', stock_id)
                qualified_candidates.append(f"{status} {stock_id} {name}")
            except:
                continue

        # Firebase 寫入
        fb_config = os.environ.get('FIREBASE_CONFIG')
        if fb_config and not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(fb_config))
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})

        db.reference('stock_alerts/bot_1').set({
            'bot_name': '🚀 機器人一號：持股營收哨兵',
            'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': qualified_candidates if qualified_candidates else ["監控標的暫無雙增"],
            'criteria': '監控持股：連續 4 月營收雙增 (FinMind 授權版)'
        })
        print(f"🏁 一號機執行完畢")
    except Exception as e:
        print(f"❌ 一號機故障: {e}")

if __name__ == "__main__":
    run_sentinel_strategy()

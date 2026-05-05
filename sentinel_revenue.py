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
    today_str = tw_now.strftime("%Y-%m-%d")
    print(f"--- 🚀 機器人一號：持股營收監控啟動 ({today_str}) ---")

    # 1. 初始化 FinMind
    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN', '')
    if token:
        api.login_token(token)

    # 【自定義監控清單】在此輸入你的持股代碼
    my_stocks = ["2330", "2317", "2454", "0050", "0056"] 
    
    # 抓取過去 180 天的資料，確保能比對連續 4 個月
    start_date = (tw_now - timedelta(days=180)).strftime("%Y-%m-%d")
    
    qualified_candidates = []
    
    try:
        for stock_id in my_stocks:
            try:
                # 抓取單一股票營收
                df = api.taiwan_stock_month_revenue(
                    stock_id=stock_id,
                    start_date=start_date
                )
                
                if df.empty or len(df) < 4:
                    continue
                
                # 排序並取得最後 4 個月
                df = df.sort_values('date')
                recent_4 = df.tail(4)
                
                # 判斷是否連續 4 月雙增 (YoY > 1% 且 MoM > 1%)
                is_qualified = True
                for _, row in recent_4.iterrows():
                    mom = row.get('revenue_month_growth_percent', 0)
                    yoy = row.get('revenue_year_growth_percent', 0)
                    if mom < 1 or yoy < 1:
                        is_qualified = False
                        break
                
                status_icon = "🔥" if is_qualified else "⚪"
                stock_name = df.iloc[-1].get('stock_name', stock_id)
                qualified_candidates.append(f"{status_icon} {stock_id} {stock_name}")
                
            except Exception as e:
                print(f"⚠️ 處理 {stock_id} 時發生錯誤: {e}")
                continue

        # 2. Firebase 初始化與寫入
        fb_config_str = os.environ.get('FIREBASE_CONFIG')
        if fb_config_str and not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(fb_config_str))
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})

        # 3. 更新 App 顯示區
        db.reference('stock_alerts/bot_1').set({
            'bot_name': '🚀 機器人一號：持股營收哨兵',
            'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': qualified_candidates if qualified_candidates else ["目前監控持股暫無雙增訊號"],
            'criteria': f"針對清單 {len(my_stocks)} 檔持股，監控是否連續 4 月雙增"
        })
        
        print(f"🏁 掃描完成，監控中：{len(my_stocks)} 檔")

    except Exception as e:
        print(f"❌ 一號機器人 (監控模式) 故障：{e}")

if __name__ == "__main__":
    run_sentinel_strategy()

import os
import json
import firebase_admin
from firebase_admin import credentials, db
from FinMind.data import DataLoader
from datetime import datetime, timedelta, timezone

def get_taiwan_time():
    """取得台灣時間 (UTC+8)"""
    return datetime.now(timezone.utc) + timedelta(hours=8)

def run_sentinel_strategy():
    tw_now = get_taiwan_time()
    print(f"--- 🚀 機器人一號：持股營收哨兵啟動 ({tw_now.strftime('%Y-%m-%d %H:%M:%S')}) ---")

    # 1. 初始化環境與登入
    api = DataLoader()
    raw_token = os.environ.get('FINMIND_TOKEN', '')
    token = raw_token.strip().replace("'", "").replace('"', "")
    
    if not token:
        print("❌ 錯誤：找不到 FINMIND_TOKEN，請檢查 GitHub Secrets 設定")
        return
    api.login_by_token(api_token=token)

    # 2. 設定參數
    my_stocks = ["2330", "2337", "2454", "2308", "2317", "7794", "2072"]
    start_date = (tw_now - timedelta(days=550)).strftime("%Y-%m-%d")
    qualified_candidates = []
    
    # 3. 核心篩選迴圈
    for stock_id in my_stocks:
        try:
            df = api.taiwan_stock_month_revenue(
                stock_id=stock_id,
                start_date=start_date
            )
            
            if df.empty or len(df) < 13:
                print(f"⚠️ {stock_id}：歷史資料不足以計算 YoY (需要至少 13 個月)")
                continue
            
            df = df.sort_values('date')
            
            # 正確計算年增率 (YoY)
            df['revenue_year_growth_percent'] = df['revenue'].pct_change(periods=12) * 100

            # 拿最後 4 個月來判定
            recent_4_df = df.dropna(subset=['revenue_year_growth_percent']).tail(4)
            
            if len(recent_4_df) < 4:
                print(f"⚠️ {stock_id}：計算後可用的最近資料不足 4 筆")
                continue

            yoy_list = [round(x, 2) for x in recent_4_df['revenue_year_growth_percent'].tolist()]
            print(f"🔍 檢查 {stock_id} 最近 4 月正確 YoY: {yoy_list}")

            # 判斷條件：連續 4 個月年增率 > 1%
            is_qualified = all(yoy > 1 for yoy in yoy_list)
            
            status = "🔥" if is_qualified else "⚪"
            name = df.iloc[-1].get('stock_name', stock_id)
            qualified_candidates.append(f"{status} {stock_id} {name}")
            print(f"{status} {stock_id} 判定完成")

        except Exception as e:
            print(f"❌ {stock_id} 處理時發生錯誤: {e}")

    # 4. 全部跑完後，一次性寫入 Firebase
    try:
        print(f"📡 即將寫入 Firebase 的最終名單: {qualified_candidates}")
        
        fb_config_str = os.environ.get('FIREBASE_CONFIG')
        if fb_config_str and not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(fb_config_str))
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'
            })

        if firebase_admin._apps:
            db.reference('stock_alerts/bot_1').set({
                'bot_name': '🚀 機器人一號：持股營收哨兵',
                'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
                'candidates': qualified_candidates if qualified_candidates else ["暫無雙增標的"],
                'criteria': '監控持股：連續 4 月營收年增 > 1%'
            })
            print(f"🏁 Firebase 資料寫入成功")
            
    except Exception as fb_e:
        print(f"❌ Firebase 寫入失敗: {fb_e}")

if __name__ == "__main__":
    run_sentinel_strategy()

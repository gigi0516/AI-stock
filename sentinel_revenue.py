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
    print(f"--- 🚀 機器人一號：FinMind 全市場營收掃描啟動 ({today_str}) ---")

    # 1. 初始化 FinMind
    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN', '') # 確保 GitHub Secrets 有設定這個
    if token:
        api.login_token(token)

    # 抓取過去 150 天的資料，足以涵蓋連續 4 個月的比較
    start_date = (tw_now - timedelta(days=150)).strftime("%Y-%m-%d")
    
    try:
        # [關鍵修正]：不傳入 stock_id，FinMind 會回傳該段時間內全市場的資料
        df = api.taiwan_stock_month_revenue(start_date=start_date)
        
        if df.empty:
            print("❌ 無法從 FinMind 取得營收資料")
            return

        qualified_candidates = []
        
        # 2. 核心邏輯：依股票代碼分組計算連續雙增
        for stock_id, group in df.groupby('stock_id'):
            group = group.sort_values('date')
            
            # 必須有至少 4 個月的資料
            if len(group) < 4:
                continue
                
            recent_4_months = group.tail(4)
            
            # 判斷連續 4 個月雙增 (YoY > 1% 且 MoM > 1%)
            is_qualified = True
            for _, row in recent_4_months.iterrows():
                # FinMind 提供的增長率欄位
                mom = row.get('revenue_month_growth_percent', 0)
                yoy = row.get('revenue_year_growth_percent', 0)
                
                if mom < 1 or yoy < 1:
                    is_qualified = False
                    break
            
            if is_qualified:
                stock_name = group.iloc[-1].get('stock_name', '')
                qualified_candidates.append(f"{stock_id} {stock_name}")

        # 3. Firebase 初始化 (請務必檢查 Secrets)
        fb_config_str = os.environ.get('FIREBASE_CONFIG')
        if not fb_config_str:
            print("❌ 找不到 FIREBASE_CONFIG")
            return
            
        if not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(fb_config_str))
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})

        # 4. 更新 App 顯示區
        db.reference('stock_alerts/bot_1').set({
            'bot_name': '🚀 機器人一號：長線營收王',
            'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': qualified_candidates if qualified_candidates else ["今日尚未發現連續 4 月雙增標的"],
            'criteria': '長線趨勢：連續 4 個月營收雙增 (FinMind 全市場掃描)'
        })
        
        print(f"🏁 掃描完成，符合條件：{len(qualified_candidates)} 檔")

    except Exception as e:
        print(f"❌ 一號機器人執行失敗：{e}")

if __name__ == "__main__":
    run_sentinel_strategy()

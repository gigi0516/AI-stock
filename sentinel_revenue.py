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
    
    # --- 修正：自動清除 Token 可能含有的引號或空格 ---
    raw_token = os.environ.get('FINMIND_TOKEN', '')
    token = raw_token.strip().replace("'", "").replace('"', "")
    
    if not token:
        print("❌ 錯誤：找不到 FINMIND_TOKEN，請檢查 GitHub Secrets 設定")
        return

    # 登入
    api.login_by_token(api_token=token)
    # --------------------------------------------

    my_stocks = ["2330", "2337", "2454", "2308", "2317", "7794", "2072"]
    start_date = (tw_now - timedelta(days=180)).strftime("%Y-%m-%d")
    qualified_candidates = []
    
    # 3. 核心篩選迴圈 (注意縮排)
    for stock_id in my_stocks:
        try:
            df = api.taiwan_stock_month_revenue(
                stock_id=stock_id,
                start_date=start_date
            )
            
            if df.empty or len(df) < 4:
                print(f"⚠️ {stock_id}：資料不足或為空 (抓到 {len(df)} 筆)")
                continue
            
            # 【診斷點】印出欄位名稱，看看真正的名稱是什麼
            print(f"📊 {stock_id} 抓到的欄位有: {df.columns.tolist()}")
            
            df = df.sort_values('date')
            recent_4 = df.tail(4)
            
            # 【相容性處理】檢查年增率欄位的正確名稱
            # 有些版本是 'revenue_year_growth_percent'，有些是 'revenue_year_growth'
            target_col = 'revenue_year_growth_percent'
            if target_col not in df.columns:
                if 'revenue_year_growth' in df.columns:
                    target_col = 'revenue_year_growth'
                else:
                    # 如果都找不到，就印出錯誤並跳過
                    print(f"❌ {stock_id} 找不到年增率欄位")
                    continue

            yoy_list = recent_4[target_col].tolist()
            print(f"🔍 檢查 {stock_id} 最近 4 月 YoY: {yoy_list}")

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
if __name__ == "__main__":
    run_sentinel_strategy()

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
                print(f"⚠️ {stock_id}：資料不足 (抓到 {len(df)} 筆)")
                continue
            
            # --- 【核心修正】手動計算年增率 ---
            # 如果 API 沒給百分比，我們就用 (當月營收 - 去年同月) / 去年同月 * 100
            if 'revenue_year_growth_percent' not in df.columns:
                df['revenue_year_growth_percent'] = (
                    (df['revenue'] - df['revenue_year']) / df['revenue_year'] * 100
                )
            # -------------------------------

            df = df.sort_values('date')
            recent_4 = df.tail(4)
            
            # 診斷點：現在這裡絕對會有數字了！
            yoy_list = [round(x, 2) for x in recent_4['revenue_year_growth_percent'].tolist()]
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

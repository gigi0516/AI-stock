import requests
import os
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta, timezone

def get_taiwan_time():
    return datetime.now(timezone.utc) + timedelta(hours=8)

def run_sentinel_strategy():
    tw_now = get_taiwan_time()
    today_str = tw_now.strftime("%Y-%m-%d")
    print(f"--- 🚀 機器人一號：OpenAPI 營收監控啟動 ({today_str}) ---")

    # 1. 抓取證交所：申報當月營收彙總表 (TWE044U)
    url = "https://openapi.twse.com.tw/v1/statistics/TWE044U"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            print("❌ 無法取得證交所營收資料")
            return
        
        data = response.json()
        # --- 段落：台股休市判斷 ---
        tw_now = get_taiwan_time()
    # 第一層：過濾週末
        if tw_now.weekday() >= 5:
            print(f"☕ 台灣時間 {tw_now.strftime('%Y-%m-%d')} 是週末，機器人放假去！")
            return

    # 第二層：過濾國定假日 (由 OpenAPI 資料是否為空來判斷)
    # 執行 requests.get 後加入這行：
        if not data or len(data) == 0:
                print(f"😴 今日 ({tw_now.strftime('%Y-%m-%d')}) 證交所未產出資料，應為休市日。")
                return
        # 2. Firebase 初始化
        fb_config = os.environ.get('FIREBASE_CONFIG')
        if not fb_config: 
            print("❌ 找不到 FIREBASE_CONFIG")
            return
            
        if not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(fb_config))
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})

        qualified_candidates = []
        
        # 3. 處理每一檔股票
        for item in data:
            try:
                code = item.get('StockCode')
                name = item.get('StockName', '').strip()
                
                # 取得數值 (當月、上月、去年同月)
                rev_now = float(item.get('RevenueCurrentMonth', 0))
                rev_last_month = float(item.get('RevenueLastMonth', 0))
                rev_last_year = float(item.get('RevenueSameMonthLastYear', 0))
                
                # 取得資料所屬月份 (例如 "114/3")
                current_data_month = item.get('CurrentMonth', '')

                # 雙增判斷 (YoY > 1% 且 MoM > 1%)
                is_growing = (rev_now > rev_last_month * 1.01) and (rev_now > rev_last_year * 1.01)

                # 讀取 Firebase 紀錄的歷史狀態
                history_ref = db.reference(f'bot_1_history/{code}')
                history_data = history_ref.get() or {"count": 0, "last_month": ""}
                
                new_count = history_data.get("count", 0)

                # 如果這是「新的月份」資料
                if history_data.get("last_month") != current_data_month:
                    if is_growing:
                        new_count += 1
                    else:
                        new_count = 0 # 沒達成，歸零重計
                    # 更新歷史紀錄
                    history_ref.set({"count": new_count, "last_month": current_data_month})
                
                # 如果連續達成 4 個月，加入名單
                if new_count >= 4:
                    qualified_candidates.append(f"{code} {name}")
                    
            except Exception:
                continue

        # 4. 更新 App 顯示區
        db.reference('stock_alerts/bot_1').set({
            'bot_name': '🚀 機器人一號：長線營收王',
            'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': qualified_candidates if qualified_candidates else ["今日尚未發現連續 4 月雙增標的"],
            'criteria': '長線趨勢：連續 4 個月營收雙增 (OpenAPI 自動累計)'
        })
        
        print(f"🏁 掃描完成，符合條件：{len(qualified_candidates)} 檔")

    except Exception as e:
        print(f"❌ 一號機器人發生故障：{e}")

# --- 程式入口 ---
if __name__ == "__main__":
    run_sentinel_strategy()

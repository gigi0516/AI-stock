import requests
import os
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta, timezone

def get_taiwan_time():
    # 強制取得台灣時間 (UTC+8)
    return datetime.now(timezone.utc) + timedelta(hours=8)

def run_sentinel_strategy():
    tw_now = get_taiwan_time()
    today_str = tw_now.strftime("%Y-%m-%d")
    
    # [修正] 第一步：先判斷週末，如果是週末就直接結束，不要連網
    if tw_now.weekday() >= 5:
        print(f"☕ 台灣時間 {today_str} 是週末，機器人放假去！")
        return

    print(f"--- 🚀 機器人一號：OpenAPI 營收監控啟動 ({today_str}) ---")

    # 使用 OpenAPI：申報當月營收彙總表 (TWE044U)
    url = "https://openapi.twse.com.tw/v1/statistics/TWE044U"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        # [加強保護]：加上 Headers 與 Timeout
        response = requests.get(url, headers=headers, timeout=30)
        
        # [關鍵修正]：攔截空內容，防止 json() 報錯 (char 0 錯誤就在這發生)
        if response.status_code != 200 or not response.text.strip():
            print(f"😴 今日 ({today_str}) 證交所未產出資料，應為休市日或尚未更新。")
            return
        
        try:
            data = response.json()
        except Exception:
            print("❌ 證交所回傳格式錯誤 (非 JSON)，跳過本次執行。")
            return

        if not data or len(data) == 0:
            print(f"😴 今日 ({today_str}) 證交所資料為空，應為休市日。")
            return

        # 2. Firebase 初始化 (安全檢查)
        fb_config_str = os.environ.get('FIREBASE_CONFIG')
        if not fb_config_str: 
            print("❌ 找不到 FIREBASE_CONFIG")
            return
            
        if not firebase_admin._apps:
            try:
                cred = credentials.Certificate(json.loads(fb_config_str))
                firebase_admin.initialize_app(cred, {
                    'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'
                })
            except Exception as e:
                print(f"❌ Firebase 初始化失敗: {e}")
                return

        qualified_candidates = []
        
        # 3. 處理每一檔股票 (原本邏輯保持不變)
        for item in data:
            try:
                code = item.get('StockCode')
                if not code: continue
                name = item.get('StockName', '').strip()
                
                rev_now = float(item.get('RevenueCurrentMonth', 0))
                rev_last_month = float(item.get('RevenueLastMonth', 0))
                rev_last_year = float(item.get('RevenueSameMonthLastYear', 0))
                current_data_month = item.get('CurrentMonth', '')

                # 雙增判斷 (YoY > 1% 且 MoM > 1%)
                is_growing = (rev_now > rev_last_month * 1.01) and (rev_now > rev_last_year * 1.01)

                # 讀取歷史狀態
                history_ref = db.reference(f'bot_1_history/{code}')
                history_data = history_ref.get() or {"count": 0, "last_month": ""}
                new_count = history_data.get("count", 0)

                if history_data.get("last_month") != current_data_month:
                    if is_growing:
                        new_count += 1
                    else:
                        new_count = 0
                    history_ref.set({"count": new_count, "last_month": current_data_month})
                
                if new_count >= 4:
                    qualified_candidates.append(f"{code} {name}")
                    
            except Exception:
                continue

        # 4. 更新 App 顯示區 (注意路徑與 App 內一致)
        db.reference('stock_alerts/bot_1').set({
            'bot_name': '🚀 機器人一號：長線營收王',
            'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': qualified_candidates if qualified_candidates else ["今日尚未發現連續 4 月雙增標的"],
            'criteria': '長線趨勢：連續 4 個月營收雙增'
        })
        
        print(f"🏁 掃描完成，符合條件：{len(qualified_candidates)} 檔")

    except Exception as e:
        print(f"❌ 一號機器人發生嚴重故障：{e}")

if __name__ == "__main__":
    run_sentinel_strategy()

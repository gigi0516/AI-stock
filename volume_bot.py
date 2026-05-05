import requests
import os
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta, timezone

def get_taiwan_time():
    return datetime.now(timezone.utc) + timedelta(hours=8)

def run_bot_2_strategy():
    # --- 1. 時間判斷 (第一層：過濾週末) ---
    tw_now = get_taiwan_time()
    today_str = tw_now.strftime("%Y-%m-%d")
    
    if tw_now.weekday() >= 5:
        print(f"☕ 台灣時間 {today_str} 是週末，機器人放假去！")
        return

    print(f"--- 🚀 機器人二號：開始全市場量能爆發掃描 ({today_str}) ---")
    
    # 2. 抓取今日成交資料
    
    url = "https://openapi.twse.com.tw/v1/fund/T86W0"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        # 執行網路請求
        response = requests.get(url, headers=headers, timeout=30)
        data = response.json()
        
        # --- 3. 休市判斷 (第二層：過濾國定假日) ---
        # 如果證交所 API 回傳空內容，代表今日休市
        if not data or len(data) == 0:
            print(f"😴 今日 ({today_str}) 證交所未產出資料，應為休市日。")
            return

        today_vol_map = {}
        potential_candidates = []

        # 4. Firebase 初始化
        fb_config = os.environ.get('FIREBASE_CONFIG')
        if not fb_config: 
            print("❌ 找不到 FIREBASE_CONFIG")
            return
            
        if not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(fb_config))
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})
        
        history_ref = db.reference('bot_2_history/last_volume')
        yesterday_vol_map = history_ref.get() or {}

        # 5. 開始比對爆量邏輯
        for item in data:
            code = item.get('Code')
            name = item.get('Name', '').strip()
            try:
                # 取得今日量與昨日量 (轉張數)
                raw_vol = item.get('TradeVolume', '0').replace(',', '')
                today_vol = int(raw_vol) // 1000 
                yesterday_vol = yesterday_vol_map.get(code, 0)
                
                # 紀錄今天量，準備給明天用
                today_vol_map[code] = today_vol

                # 篩選條件：今日 > 2000張、量增2倍、漲幅為正
                change_str = item.get('Change', '0').replace(',', '')
                change = float(change_str)
                
                if today_vol > 2000 and yesterday_vol > 0:
                    if today_vol > (yesterday_vol * 2) and change > 0:
                        potential_candidates.append(f"{code} {name}")
                        print(f"🔥 爆量發現: {code} {name} (今:{today_vol} / 昨:{yesterday_vol})")
            except:
                continue

        # 6. 更新 Firebase 顯示區
        db.reference('stock_alerts/bot_2').set({
            'bot_name': '🚀 機器人二號：短線量能爆發',
            'last_update': tw_now.strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': potential_candidates if potential_candidates else ["今日尚無量能翻倍標的"],
            'criteria': '短線爆發：今日成交量 > 昨日 2 倍 且 股價收紅'
        })

        # 7. 更新歷史量能紀錄 (儲存今日量給明天比對用)
        history_ref.set(today_vol_map)
        print(f"🏁 二號機器人掃描完成，發現 {len(potential_candidates)} 檔。")

    except Exception as e:
        print(f"❌ 二號機器人執行失敗: {e}")

if __name__ == "__main__":
    run_bot_2_strategy()

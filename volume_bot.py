import requests
import os
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta, timezone

def get_taiwan_time():
    return datetime.now(timezone.utc) + timedelta(hours=8)

def run_bot_2_strategy():
    tw_now = get_taiwan_time()
    today_str = tw_now.strftime("%Y-%m-%d")
    
    # 1. 週末直接收工
    if tw_now.weekday() >= 5:
        print("☕ 週末休市中，不執行。")
        return

    print(f"--- 🚀 機器人二號：開始全市場量能爆發掃描 ({today_str}) ---")
    
    # 2. 抓取資料
    url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        data = response.json()

        # 3. 判斷是否休市（沒資料回傳）
        if not data or len(data) == 0:
            print(f"😴 今天 ({today_str}) 台股休市或尚未產出資料，機器人先去休息囉！")
            return

        # 4. 初始化
        today_vol_map = {}
        potential_candidates = []

        # 5. Firebase 初始化
        fb_config = os.environ.get('FIREBASE_CONFIG')
        if not fb_config: 
            print("❌ 找不到 FIREBASE_CONFIG")
            return

        if not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(fb_config))
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})
        
        history_ref = db.reference('bot_2_history/last_volume')
        yesterday_vol_map = history_ref.get() or {}

        # 6. 比對邏輯
        for item in data:
            code = item.get('Code')
            name = item.get('Name', '').strip()
            try:
                # 取得今日成交量 (張)
                today_vol = int(item.get('TradeVolume', '0').replace(',', '')) // 1000
                yesterday_vol = yesterday_vol_map.get(code, 0)
                
                # 紀錄今天量，準備給明天用
                today_vol_map[code] = today_vol

                # 漲跌幅處理
                change_str = item.get('Change', '0')
                change = float(change_str) if change_str.strip() else 0
                
                # 條件：今日 > 2000張、量增2倍、漲
                if today_vol > 2000 and yesterday_vol > 0:
                    if today_vol > (yesterday_vol * 2) and change > 0:
                        potential_candidates.append(f"{code} {name}")
                        print(f"🔥 爆量發現: {code} {name} (今:{today_vol} / 昨:{yesterday_vol})")
            except:
                continue

        # 7. 更新 Firebase
        db.reference('stock_alerts/bot_2').set({
            'bot_name': '🚀 機器人二號：短線量能爆發',
            'last_update': tw_now.strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': potential_candidates if potential_candidates else ["今日尚無量能翻倍標的"],
            'criteria': '短線爆發：今日成交量 > 昨日 2 倍 且 股價收紅'
        })

        # 8. 儲存今日交易量供下次比對
        history_ref.set(today_vol_map)
        print(f"🏁 二號機器人掃描完成，發現 {len(potential_candidates)} 檔。")

    except Exception as e:
        print(f"❌ 二號機器人執行失敗: {e}")

if __name__ == "__main__":
    run_bot_2_strategy()

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
    if tw_now.weekday() >= 5:
        print("週末不執行二號掃描")
        return

    print("--- 🚀 機器人二號：開始全市場量能爆發掃描 ---")
    
    # 1. 抓取今日成交資料
    url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        data = response.json()
        
        today_vol_map = {}
        potential_candidates = []

        # 2. 獲取 Firebase 紀錄的「昨天成交量」
        fb_config = os.environ.get('FIREBASE_CONFIG')
        if not fb_config: return
        if not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(fb_config))
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})
        
        history_ref = db.reference('bot_2_history/last_volume')
        yesterday_vol_map = history_ref.get() or {}

        # 3. 開始比對
        for item in data:
            code = item.get('Code')
            name = item.get('Name').strip()
            try:
                # 取得今日量與昨日量
                today_vol = int(item.get('TradeVolume', '0')) // 1000 # 轉張數
                yesterday_vol = yesterday_vol_map.get(code, 0)
                
                # 紀錄今天量，準備給明天用
                today_vol_map[code] = today_vol

                # 篩選門檻
                # - 今日 > 2000 張
                # - 今日 > 昨天 2 倍
                # - 漲幅 (Change) 為正數
                change = float(item.get('Change', '0'))
                
                if today_vol > 2000 and yesterday_vol > 0:
                    if today_vol > (yesterday_vol * 2) and change > 0:
                        potential_candidates.append(f"{code} {name}")
                        print(f"🔥 爆量發現: {code} {name} (今:{today_vol} / 昨:{yesterday_vol})")
            except:
                continue

        # 4. 更新 Firebase
        # 更新給 App 看的名單
        db.reference('stock_alerts/bot_2').set({
            'bot_name': '🚀 機器人二號：短線量能爆發',
            'last_update': tw_now.strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': potential_candidates if potential_candidates else ["今日尚無量能翻倍標的"],
            'criteria': '短線爆發：今日成交量 > 昨日 2 倍 且 股價收紅'
        })

        # 更新歷史量能紀錄 (給明天比對用)
        history_ref.set(today_vol_map)
        
        print(f"🏁 二號機器人掃描完成，發現 {len(potential_candidates)} 檔。")

    except Exception as e:
        print(f"❌ 二號機器人執行失敗: {e}")

if __name__ == "__main__":
    run_bot_2_strategy()

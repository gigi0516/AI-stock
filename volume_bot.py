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
    
    url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
def run_bot_2_strategy():
    # --- 新增這段判斷 ---
    tw_now = get_taiwan_time()
    today_str = tw_now.strftime("%Y-%m-%d")
    
    # 週末直接收工 (雖然 YAML 過濾了，但 Python 雙重保險更好)
    if tw_now.weekday() >= 5:
        print("☕ 週末休市中，不執行。")
        return

    # 抓取資料後判斷是否為空
    url = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
    response = requests.get(url, timeout=30)
    data = response.json()

    if not data or len(data) == 0:
        print(f"😴 今天 ({today_str}) 台股休市或尚未產出資料，機器人先去休息囉！")
        return
   
        return
        today_vol_map = {}
        potential_candidates = []

        fb_config = os.environ.get('FIREBASE_CONFIG')
        if not fb_config: return
        if not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(fb_config))
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})
        
        history_ref = db.reference('bot_2_history/last_volume')
        yesterday_vol_map = history_ref.get() or {}

        for item in data:
            code = item.get('Code')
            name = item.get('Name', '').strip()
            try:
                today_vol = int(item.get('TradeVolume', '0').replace(',', '')) // 1000
                yesterday_vol = yesterday_vol_map.get(code, 0)
                today_vol_map[code] = today_vol

                # 篩選：量增 2 倍且漲 (Change > 0) 且量 > 2000
                change_str = item.get('Change', '0')
                change = float(change_str) if change_str != ' ' else 0
                
                if today_vol > 2000 and yesterday_vol > 0:
                    if today_vol > (yesterday_vol * 2) and change > 0:
                        potential_candidates.append(f"{code} {name}")
                        print(f"🔥 爆量發現: {code} {name} (今:{today_vol} / 昨:{yesterday_vol})")
            except:
                continue

        # --- 這裡就是你原本報錯的縮排區塊 ---
        db.reference('stock_alerts/bot_2').set({
            'bot_name': '🚀 機器人二號：短線量能爆發',
            'last_update': tw_now.strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': potential_candidates if potential_candidates else ["今日尚無量能翻倍標的"],
            'criteria': '短線爆發：今日成交量 > 昨日 2 倍 且 股價收紅'
        })

        history_ref.set(today_vol_map)
        print(f"🏁 二號機器人掃描完成，發現 {len(potential_candidates)} 檔。")

    except Exception as e:
        print(f"❌ 二號機器人執行失敗: {e}")

if __name__ == "__main__":
    run_bot_2_strategy()

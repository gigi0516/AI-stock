import requests
import os
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

def run_bot_4_strategy():
    print("--- 🚀 機器人四號：開始全市場法人淨買超掃描 ---")
    
    # 1. 從證交所 OpenAPI 抓取今日所有股票的法人買賣超
    # URL 是你截圖中對應的「三大法人買賣超日報」
    url = "https://openapi.twse.com.tw/v1/fund/T86W0"
    response = requests.get(url)
    if response.status_code != 200:
        print("❌ 無法取得證交所資料")
        return
    
    data = response.json()
    
    # 2. 篩選出『今日淨買超』的股票 (外資+投信 > 0)
    today_net_buy_list = []
    for item in data:
        try:
            # 取得外資與投信買賣超張數 (需處理逗點)
            foreign = int(item['ForeignInvestorsBuySellDiff'].replace(',', ''))
            sitc = int(item['InvestmentTrustBuySellDiff'].replace(',', ''))
            
            if (foreign + sitc) > 0:
                today_net_buy_list.append(item['Code'])
        except:
            continue

    # 3. 處理 Firebase 的「連續紀錄」
    update_and_check_continuous(today_net_buy_list)

def update_and_check_continuous(today_list):
    fb_config = os.environ.get('FIREBASE_CONFIG')
    if not fb_config: return
    
    # 初始化 Firebase (如果尚未初始化)
    if not firebase_admin._apps:
        cred = credentials.Certificate(json.loads(fb_config))
        firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})
    
    # --- 連續性檢查邏輯 ---
    # 我們把資料存在 history/day_1 (昨天) 和 history_day_2 (前天)
    hist_ref = db.reference('bot_4_history')
    yesterday = hist_ref.child('day_1').get() or []
    the_day_before = hist_ref.child('day_2').get() or []
    
    # 找出「今天有」、「昨天也有」、「前天也有」的交集
    final_candidates = list(set(today_list) & set(yesterday) & set(the_day_before))
    
    # 如果名單太長，我們回頭去抓這些股票的名稱 (或直接存代碼)
    # 這裡為了簡單，我們先存符合條件的代碼
    
    # 4. 更新 Firebase 給 Android App 看的結果
    db.reference('stock_alerts/bot_4').set({
        'bot_name': '🚀 機器人四號：法人連續三日買超',
        'last_update': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'candidates': final_candidates if final_candidates else ["今日尚無連續三日買超標的"],
        'criteria': '全市場掃描：外資與投信連續三個交易日皆為淨買超'
    })
    
    # 5. 重要：把歷史紀錄往後推一天，準備給明天用
    hist_ref.update({
        'day_2': yesterday,  # 昨天的變前天的
        'day_1': today_list  # 今天的變昨天的
    })
    
    print(f"🏁 掃描完成！符合連續三日買超共有 {len(final_candidates)} 檔。")

if __name__ == "__main__":
    run_bot_4_strategy()

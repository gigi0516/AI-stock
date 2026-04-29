import requests
import os
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

def run_bot_4_strategy():
    print("--- 🚀 機器人四號：開始全市場法人淨買超掃描 ---")
    
    # 1. 加上 Headers 偽裝成一般瀏覽器，避免被證交所阻擋
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # 嘗試抓取完整路徑
    url = "https://openapi.twse.com.tw/v1/fund/T86W0"
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        # 檢查是否抓取成功
        if response.status_code != 200:
            print(f"❌ 抓取失敗，狀態碼: {response.status_code}")
            return

        # 這裡加上檢查，防止 response.text 是空的
        if not response.text.strip():
            print("❌ 證交所回傳了空內容")
            return

        data = response.json()
        
        # 2. 篩選出『今日淨買超』的股票 (外資+投信 > 0)
        today_net_buy_list = []
        for item in data:
            try:
                # 欄位名稱要精確對齊 OpenAPI 格式
                foreign = int(item.get('ForeignInvestorsBuySellDiff', '0').replace(',', ''))
                sitc = int(item.get('InvestmentTrustBuySellDiff', '0').replace(',', ''))
                
                if (foreign + sitc) > 0:
                    today_net_buy_list.append(item.get('Code'))
            except:
                continue

        # 3. 處理 Firebase 邏輯
        update_and_check_continuous(today_net_buy_list)

    except requests.exceptions.JSONDecodeError:
        print("❌ 資料格式錯誤：證交所回傳的不是有效的 JSON。內容如下：")
        print(response.text[:200]) # 印出前200字看看回傳了什麼
    except Exception as e:
        print(f"❌ 發生未預料的錯誤: {e}")

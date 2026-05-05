def run_bot_4_strategy():
    tw_now = get_taiwan_time()
    today_str = tw_now.strftime("%Y-%m-%d")

    # [修正] 第一步：先判斷週末，如果是週末就直接結束，不連網
    if tw_now.weekday() >= 5:
        print(f"☕ 台灣時間 {today_str} 是週末，機器人放假去！")
        return

    print(f"--- 🚀 機器人四號：開始全市場法人淨買超掃描 ({today_str}) ---")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    # [建議]：如果 OpenAPI 不穩，建議改用正式版 API 網址 (JSON 格式稍有不同)
    # 但我們先修復現有的 OpenAPI 邏輯保護
    url = "https://openapi.twse.com.tw/v1/fund/T86W0"
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        # [加強保護]：確保有內容才解析
        if response.status_code != 200 or not response.text.strip():
            print(f"😴 今天 ({today_str}) 證交所未回傳資料，可能尚未更新或休市。")
            return

        # [修正]：使用 try-except 包裹 JSON 解析
        try:
            data = response.json()
        except Exception:
            print("❌ 證交所回傳格式錯誤 (非 JSON)，跳過本次執行。")
            return
            
        if not data or not isinstance(data, list) or len(data) == 0:
            print(f"😴 今日 ({today_str}) 無法人資料。")
            return

        # 4. 篩選邏輯 (保持不變)
        today_net_buy_list = []
        for item in data:
            try:
                # 安全取得欄位內容，防止 Key 缺失
                foreign = int(item.get('ForeignInvestorsBuySellDiff', '0').replace(',', ''))
                sitc = int(item.get('InvestmentTrustBuySellDiff', '0').replace(',', ''))
                if (foreign + sitc) > 0:
                    today_net_buy_list.append(item.get('Code'))
            except:
                continue

        print(f"✅ 今日法人有買進標的共 {len(today_net_buy_list)} 檔")

        # 5. Firebase 初始化 (修正 Config 讀取)
        fb_config_str = os.environ.get('FIREBASE_CONFIG')
        if not fb_config_str:
            print("❌ 找不到 FIREBASE_CONFIG 環境變數")
            return
        
        if not firebase_admin._apps:
            # 這裡就是報錯 char 0 的第二個可能點，補上 try-except
            try:
                fb_config = json.loads(fb_config_str)
                cred = credentials.Certificate(fb_config)
                firebase_admin.initialize_app(cred, {
                    'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'
                })
            except Exception as e:
                print(f"❌ Firebase 配置解析失敗: {e}")
                return

        update_and_check_continuous(today_net_buy_list)

    except Exception as e:
        print(f"❌ 四號機器人發生嚴重錯誤: {e}")

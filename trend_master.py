def upload_to_firebase(candidates):
    # 1. 取得 Secret
    fb_config = os.environ.get('FIREBASE_CONFIG')
    
    # 安全檢查：如果沒設定 Secret 就直接結束，不要往下跑
    if not fb_config:
        print("❌ 錯誤：GitHub Secrets 中找不到 'FIREBASE_CONFIG'，請確認名稱是否打錯。")
        return

    try:
        # 2. 解析 JSON
        cred_json = json.loads(fb_config)
        
        # 3. 初始化 Firebase (確保 cred 在這裡定義)
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_json) # 這裡定義了 cred
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'
            })
        
        # 4. 寫入資料
        ref = db.reference('stock_alerts/trend_master')
        ref.set({
            'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': candidates,
            'status': 'Success'
        })
        print(f"📢 Firebase 同步成功！名單：{candidates}")

    except Exception as e:
        print(f"❌ Firebase 處理異常: {e}")

if __name__ == "__main__":
    result = run_full_strategy()
    print(f"✅ 最終精選名單: {result}")
    
    # 只有名單不是空的時候才執行上傳（或者你想測試空名單也可以）
    upload_to_firebase(result)

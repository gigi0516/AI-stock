import yfinance as yf
import os
import json
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime, timedelta, timezone

def get_taiwan_time():
    return datetime.now(timezone.utc) + timedelta(hours=8)

def run_bot_3_strategy():
    print("--- 🚀 機器人三號：哆啦A夢美股情報局啟動 ---")
    
    try:
        # 1. 抓取數據 (下載最近 5 天以確保跨過週末)
        tickers = ["^VIX", "^IXIC"]
        data = yf.download(tickers, period="5d", interval="1d")
        
        if data.empty or len(data) < 2:
            print("💡 資料庫目前沒東西，哆啦A夢先去睡午覺了...")
            return

        # --- 核心修正：處理 MultiIndex 並過濾 NaN ---
        # 使用 .dropna() 確保我們只拿有數值的日期
        close_prices = data['Close'].dropna()
        
        if len(close_prices) < 2:
            print("⚠️ 數值不足，無法計算漲跌。")
            return

        # 2. 取得最新與次新資料
        # iloc[-1] 是最新, iloc[-2] 是前一天
        vix_val = round(float(close_prices['^VIX'].iloc[-1]), 2)
        nasdaq_now = float(close_prices['^IXIC'].iloc[-1])
        nasdaq_prev = float(close_prices['^IXIC'].iloc[-2])
        
        nasdaq_chg = round(((nasdaq_now - nasdaq_prev) / nasdaq_prev) * 100, 2)

        # 3. 哆啦A夢情境邏輯 (保持不變)
        header = "🔵【大雄！我從未來帶回美股消息了！】\n"
        
        if vix_val < 20:
            vix_mood = f"🍵 目前 VIX 是 {vix_val}，市場非常穩定喔！"
            vix_advice = "就像在靜香家喝下午茶一樣安心。大雄，我們可以用『竹蜻蜓』輕鬆看待盤勢！"
        elif 20 <= vix_val < 30:
            vix_mood = f"🧐 嘿... VIX 來到 {vix_val}，稍微有點不穩定。"
            vix_advice = "感覺胖虎就在附近唱歌... 有點風吹草動。拿好『放大燈』仔細盯著看，別亂衝喔！"
        elif 30 <= vix_val < 40:
            vix_mood = f"😰 糟糕！VIX 衝到 {vix_val}，市場很不穩定！"
            vix_advice = "哇啊！胖虎拿著棒球棍衝過來了啦！快去搭『時光機』回防，這時候很危險的！"
        else:
            vix_mood = f"😱 救命啊！VIX 爆表到 {vix_val}，這是極度恐慌狀態！"
            vix_advice = "大雄！世界末日啦！快披上『避難斗篷』躲進書桌抽屜！不管看到什麼都不要動！"

        market_summary = f"那斯達克漲跌：{nasdaq_chg}%"
        
        if nasdaq_chg > 1.2 and vix_val < 30:
            final_advice = f"{vix_advice} 而且那指噴出了，明天台股電子股可能會有好表現喔！"
        elif nasdaq_chg < -1.5:
            final_advice = f"{vix_advice} 加上科技股跌很慘，大雄你先用『記憶吐司』複習教訓，別亂動！"
        else:
            final_advice = vix_advice

        final_report = f"{header}{vix_mood}\n{market_summary}\n\n🤖 叮噹評語：\n{final_advice}"

        # 4. 推送到 Firebase
        fb_config = os.environ.get('FIREBASE_CONFIG')
        if not fb_config: return
        
        if not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(fb_config))
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})
        
        db.reference('stock_alerts/bot_3').set({
            'bot_name': '🤖 機器人三號：小叮噹觀測員',
            'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': [final_report],
            'criteria': f'VIX分級：10-20穩定/20-30不穩/30-40焦慮/40+恐慌'
        })
        print(f"✅ 哆啦A夢報告成功：VIX={vix_val}, Nasdaq={nasdaq_chg}%")

    except Exception as e:
        print(f"❌ 三號機器人發生故障：{e}")

if __name__ == "__main__":
    run_bot_3_strategy()

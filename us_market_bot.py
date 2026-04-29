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
        # 1. 抓取數據 (必須先下載數據，後面的判斷才有用！)
        # ^VIX 是恐慌指數, ^IXIC 是那斯達克
        data = yf.download(["^VIX", "^IXIC"], period="2d", interval="1d")
        
        # --- 段落：美股休市判斷 (下載完立刻檢查) ---
        if data.empty or len(data) < 2:
            print("💡 美股目前處於休市狀態或資料尚未更新，哆啦A夢先去睡午覺了...")
            return

        # 額外保險：檢查最新資料日期是否太舊 (超過兩天沒更新)
        last_trade_date = data.index[-1].date()
        if last_trade_date < (datetime.now(timezone.utc) - timedelta(days=2)).date():
            print(f"📡 最後交易日為 {last_trade_date}，美股可能在放長假。")
            return

        # 2. 計算數值
        vix_val = round(data['Close']['^VIX'].iloc[-1], 2)
        nasdaq_now = data['Close']['^IXIC'].iloc[-1]
        nasdaq_prev = data['Close']['^IXIC'].iloc[-2]
        nasdaq_chg = round(((nasdaq_now - nasdaq_prev) / nasdaq_prev) * 100, 2)

        # 3. 哆啦A夢情境邏輯
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
        else: # 40 以上
            vix_mood = f"😱 救命啊！VIX 爆表到 {vix_val}，這是極度恐慌狀態！"
            vix_advice = "大雄！世界末日啦！快披上『避難斗篷』躲進書桌抽屜！不管看到什麼都不要動！"

        market_summary = f"那斯達克漲跌：{nasdaq_chg}%"
        
        # 結合 Nasdaq 表現補充評語
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
        print("✅ 哆啦A夢專業版回報成功！")

    except Exception as e:
        print(f"❌ 三號機器人發生故障：{e}")

if __name__ == "__main__":
    run_bot_3_strategy()

import os
import json
import firebase_admin
from firebase_admin import credentials, db
from FinMind.data import DataLoader
from datetime import datetime, timedelta, timezone

def get_taiwan_time():
    return datetime.now(timezone.utc) + timedelta(hours=8)

def run_bot_2_strategy():
    tw_now = get_taiwan_time()
    today_str = tw_now.strftime("%Y-%m-%d")
    print(f"--- 🚀 機器人二號：FinMind 量能爆發掃描啟動 ({today_str}) ---")

    api = DataLoader()
    token = os.environ.get('FINMIND_TOKEN', '')

    # 抓取最近 10 天的資料 (確保能抓到兩個完整的交易日，避開週末)
    start_date = (tw_now - timedelta(days=10)).strftime("%Y-%m-%d")
    
    try:
        # 1. 抓取全市場日成交資料
        df = api.taiwan_stock_daily_all(
            start_date=start_date,
            token=token
        )
        
        if df.empty:
            print("😴 FinMind 尚未更新今日資料。")
            return

        # 2. 找出最近的兩個交易日
        available_dates = sorted(df['date'].unique(), reverse=True)
        if len(available_dates) < 2:
            print("❌ 交易日資料不足，無法比對。")
            return
            
        latest_date = available_dates[0]
        prev_date = available_dates[1]
        print(f"📊 比對基準：今日({latest_date}) vs 昨日({prev_date})")

        today_df = df[df['date'] == latest_date]
        prev_df = df[df['date'] == prev_date]

        potential_candidates = []

        # 3. 比對爆量邏輯
        # 將昨日量轉為字典方便查詢
        prev_vol_map = dict(zip(prev_df['stock_id'], prev_df['Trading_Volume']))

        for _, row in today_df.iterrows():
            stock_id = row['stock_id']
            stock_name = row.get('stock_name', '')
            today_vol = row['Trading_Volume']
            yesterday_vol = prev_vol_map.get(stock_id, 0)
            
            # 轉換為張數 (FinMind 單位通常是股)
            today_v_shares = today_vol / 1000
            yesterday_v_shares = yesterday_vol / 1000

            # 篩選條件：今日 > 2000張、量增2倍、股價收紅 (Spread > 0)
            if today_v_shares > 2000 and yesterday_v_shares > 0:
                if today_v_shares > (yesterday_v_shares * 2) and row['Spread'] > 0:
                    potential_candidates.append(f"{stock_id} {stock_name}")
                    print(f"🔥 爆量發現: {stock_id} (今:{int(today_v_shares)} / 昨:{int(yesterday_v_shares)})")

        # 4. Firebase 更新
        fb_config = os.environ.get('FIREBASE_CONFIG')
        if fb_config and not firebase_admin._apps:
            cred = credentials.Certificate(json.loads(fb_config))
            firebase_admin.initialize_app(cred, {'databaseURL': 'https://stock-ai-a50cb-default-rtdb.firebaseio.com/'})

        db.reference('stock_alerts/bot_2').set({
            'bot_name': '🚀 機器人二號：短線量能爆發',
            'last_update': get_taiwan_time().strftime("%Y-%m-%d %H:%M:%S"),
            'candidates': potential_candidates if potential_candidates else ["今日尚無爆量標的"],
            'criteria': f'比對日期：{latest_date} | 條件：成交量 > 昨日 2 倍 且 收紅'
        })
        print(f"🏁 二號機更新完成，發現 {len(potential_candidates)} 檔")

    except Exception as e:
        print(f"❌ 二號機 (FinMind 版) 執行失敗: {e}")

if __name__ == "__main__":
    run_bot_2_strategy()

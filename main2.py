import os
import time
import logging
import requests
import re
import schedule
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# 1. 解決 Undefined 'log': 設定 Log 記錄器
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
log = logging.getLogger(__name__)

# 2. 解決 Undefined 'TELEGRAM_TOKEN' 及 'os'
# 喺 GitHub Actions 執行時，佢會去 Secrets 攞資料
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# 如果你係本機測試，可以暫時寫死佢 (正式上 GitHub 記得用返 os.getenv)
# TELEGRAM_TOKEN = "你的TOKEN"


# ═══════════════════════════════════════════════════════════
# 📡  HKEx RSS 抓取與即時監控 (補完)
# ═══════════════════════════════════════════════════════════

# 用來記錄已經處理過的公告 ID，避免重複發送
PROCESSED_FILE = "processed_ann.txt"

def get_processed_ids():
    if not os.path.exists(PROCESSED_FILE): return set()
    with open(PROCESSED_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_processed_id(ann_id):
    with open(PROCESSED_FILE, "a") as f:
        f.write(f"{ann_id}\n")

def analyse_action(title, description, code):
    """
    Placeholder: Analyse financial action from title and description
    Returns a dict with analysis results
    """
    return {
        "type": "BUY",
        "code": code,
        "title": title,
        "flags": []
    }

def enrich_with_ccass(action_res):
    """
    Placeholder: Enrich analysis with CCASS data
    """
    return {
        "code": action_res.get("code", ""),
        "type": action_res.get("type", ""),
        "grade": "A",
        "gradeLabel": "Strong Buy",
        "final": "9/10",
        "formula": "Strong Signals",
        "buy_flags": ["Positive indicator 1", "Positive indicator 2"],
        "trap_flags": ["Risk warning 1"],
        "dry_desc": "CCASS dryness indicator",
        "float_desc": "Float analysis",
        "closest": "Similar case reference",
        "action": "Suggested action based on analysis"
    }

def fetch_and_scan():
    """核心監控邏輯：抓取 -> 分析 -> 查CCASS -> 報料"""
    log.info("開始掃描 HKEx 最新公告...")
    rss_url = "https://www.hkexnews.hk/rss/news_c.xml"
    processed_ids = get_processed_ids()
    
    try:
        r = requests.get(rss_url, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
        soup = BeautifulSoup(r.content, 'xml')
        items = soup.find_all('item')
        
        for item in items:
            ann_id = item.find('guid').text if item.find('guid') else item.find('link').text
            if ann_id in processed_ids: continue
            
            title = item.find('title').text
            link = item.find('link').text
            # 提取代號 (例如: [08657])
            code_match = re.search(r'\[(\d{5})\]', title)
            if not code_match: continue
            code = code_match.group(1)
            
            # 1. 財技動作初步分析
            action_res = analyse_action(title, "", code) # RSS 通常只有標題，深度分析可點入 Link 爬全文
            
            # 2. 只有 BUY 或 INTERESTING 的才進行 CCASS 深度分析，節省 API
            if action_res["type"] in ("BUY", "MIXED", "RIGHTS"):
                full_res = enrich_with_ccass(action_res)
                send_telegram_report(full_res, link)
            
            save_processed_id(ann_id)
            time.sleep(1) # 緩衝，避免被封 IP
            
    except Exception as e:
        log.error(f"RSS 掃描失敗: {e}")

# ═══════════════════════════════════════════════════════════
# 📱  Telegram 報告模版 (視覺化優化)
# ═══════════════════════════════════════════════════════════

def send_telegram_report(res, link):
    """將分析結果格式化為師傅最愛的「驗屍報告」格式"""
    col_icon = "🟢" if res["grade"].startswith("A") else "🟡" if res["grade"].startswith("B") else "🔴"
    
    msg = f"🎯 *【財技狙擊報告 v5】* {col_icon}\n"
    msg += f"股票：[{res['code']}] {res['gradeLabel']}\n"
    msg += f"最終評分：*{res['final']}* ({res['formula']})\n"
    msg += f"------------------------\n"
    
    if res["buy_flags"]:
        msg += "✅ *正面訊號：*\n" + "\n".join([f" ▸ {f}" for f in res["buy_flags"]]) + "\n"
    
    if res["trap_flags"]:
        msg += "🚨 *風險警告：*\n" + "\n".join([f" ▸ {f}" for f in res["trap_flags"]]) + "\n"
        
    msg += f"\n📊 *CCASS 乾度分析：*\n"
    msg += f" ▸ {res['dry_desc']}\n"
    msg += f" ▸ {res['float_desc']}\n"
    
    if res["closest"]:
        msg += f"\n📚 *最接近金股案例：*\n ▸ {res['closest']}\n"
        
    msg += f"\n💡 *操作建議：*\n{res['action']}\n"
    msg += f"\n🔗 [點此查看公告原文]({link})"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown", "disable_web_page_preview": True}
    requests.post(url, data=payload)

# ═══════════════════════════════════════════════════════════
# 🚀  啟動
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    log.info("財技狙擊 Bot v5 正式啟動，正在監視老細動作...")
    # 立即執行一次
    fetch_and_scan()
    
    # 設定定時任務 (每 15 分鐘掃描一次)
    schedule.every(15).minutes.do(fetch_and_scan)
    
    while True:
        schedule.run_pending()
        time.sleep(1)

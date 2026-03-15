import requests
from bs4 import BeautifulSoup
import os
import time

# --- 1. 配置區 ---
TOKEN = "8621166491:AAGh1uJEldHphbjYxFBaFKELD6iyYvo8sGw"
CHAT_ID = os.environ.get('TG_CHAT_ID')

class HKTrickStockScanner:
    def init(self):
        # 模擬瀏覽器，防止被擋
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_ccass_data(self, ticker):
        """爬取新版 Webb-site (0xmd.com) 的持倉摘要"""
        # 修正後的 URL 格式
        url = f"https://webbsite.0xmd.com/ccass/cconc.asp?i={ticker}"
        try:
            r = requests.get(url, headers=self.headers, timeout=15)
            if r.status_code != 200: return None
            
            soup = BeautifulSoup(r.text, 'html.parser')
            # 新版網頁通常持倉百分比會喺一個叫 'otbl' 嘅表格入面
            table = soup.find('table', {'class': 'otbl'})
            if not table: return None
            
            # 抓取 Top 10 持倉
            rows = table.find_all('tr')[1:11] 
            percentages = []
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 4:
                    # 攞百分比嗰一格，除咗百分比符號
                    pct_text = cols[3].text.replace('%', '').strip()
                    percentages.append(float(pct_text))
            
            top10_total = sum(percentages) / 100
            return top10_total
        except Exception as e:
            print(f"Error scraping {ticker}: {e}")
            return None

    def evaluate(self, ticker, name, top10):
        """師傅核心：10 大財技評分系統"""
        if top10 is None: return None
        
        # 評級邏輯：>95% A+, >90% A, >80% B+
        if top10 >= 0.95:
            grade, icon = "A+", "🚨"
        elif top10 >= 0.90:
            grade, icon = "A", "🔥"
        elif top10 >= 0.80:
            grade, icon = "B+", "⏳"
        else:
            grade, icon = "B", "⚪"
            
        return {"ticker": ticker, "name": name, "top10": top10, "grade": grade, "icon": icon}

    def send_tg(self, msg):
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

def main():
    scanner = HKTrickStockScanner()
    # 師傅嘅狙擊名單 (市值 4,000萬 - 2億)
    watchlist = [
        {"code": "8657", "name": "True Partner (陳生)"},
        {"code": "8547", "name": "Pacific Legend"},
        {"code": "8238", "name": "惠陶集團"},
        {"code": "1613", "name": "協同通信"},
        {"code": "8041", "name": "林達 (AI概念)"}
    ]
    
    report = "🎯 *【財技雷達 2.1 版】新網址數據報* 🎯\n\n"
    for s in watchlist:
        top10 = scanner.get_ccass_data(s['code'])
        res = scanner.evaluate(s['code'], s['name'], top10)
        
        if res:
            report += f"{res['icon']} *[{res['ticker']}] {res['name']}*\n"
            report += f"評級: *{res['grade']}* | 歸邊度: {res['top10']:.2%}\n"
            report += f"------------------------\n"
            time.sleep(1) # 緩衝，避免被封 IP
            
    report += f"\n⏰ 報告時間: {time.strftime('%Y-%m-%d %H:%M')}\n"
    report += "💡 _數據源: webbsite.0xmd.com_"
    
    if CHAT_ID:
        scanner.send_tg(report)
        print("Done! TG 報告已送出。")
    else:
        print("Error: 未設定 TG_CHAT_ID！")

if name == "main":
    main()

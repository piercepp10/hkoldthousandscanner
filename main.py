import requests
from bs4 import BeautifulSoup
import os
import time

# 配置區
TOKEN = "8621166491:AAGh1uJEldHphbjYxFBaFKELD6iyYvo8sGw"
CHAT_ID = os.environ.get('TG_CHAT_ID')

class HKTrickStockScanner:
    def init(self):
        self.headers = {'User-Agent': 'Mozilla/5.0'}

    def get_ccass_data(self, ticker):
        """爬取 Webb-site 的持倉數據"""
        url = f"https://webb-site.com/ccass/chldchg.asp?i={ticker}"
        try:
            r = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            table = soup.find('table', {'class': 'otbl'})
            if not table: return None
            
            rows = table.find_all('tr')[1:11] # 攞前 10 名
            top10_total = sum([float(r.find_all('td')[3].text.replace('%','')) for r in rows])
            return top10_total / 100
        except:
            return None

    def evaluate(self, ticker, name, top10):
        """根據 10 大財技邏輯評分"""
        if top10 is None: return None
        
        grade = "B"
        if top10 > 0.95: grade = "A+"
        elif top10 > 0.90: grade = "A"
        elif top10 > 0.80: grade = "B+"
        
        return {
            "ticker": ticker,
            "name": name,
            "top10": top10,
            "grade": grade
        }

    def send_tg(self, msg):
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

def main():
    scanner = HKTrickStockScanner()
    watchlist = [
        {"code": "8657", "name": "True Partner (陳生)"},
        {"code": "8547", "name": "Pacific Legend"},
        {"code": "8238", "name": "惠陶集團"},
        {"code": "1613", "name": "協同通信"}
    ]
    
    report = "🎯 *【老千股雷達】每日收市驗屍報告* 🎯\n\n"
    for s in watchlist:
        top10 = scanner.get_ccass_data(s['code'])
        res = scanner.evaluate(s['code'], s['name'], top10)
        
        if res:
            fire_icon = "🔥" if res['grade'] == "A+" else "⏳"
            report += f"{fire_icon} *[{res['ticker']}] {res['name']}*\n"
            report += f"評級: {res['grade']} | 歸邊度: {res['top10']:.2%}\n"
            report += f"------------------------\n"
            
    report += f"\n⏰ 報告時間: {time.strftime('%Y-%m-%d %H:%M')}"
    
    if CHAT_ID:
        scanner.send_tg(report)
    else:
        print("未偵測到 TG_CHAT_ID，請在 GitHub Secrets 設定")

if name == "main":
    main()

import sqlite3
import os
import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "cars.db")

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS cars 
                 (ad_id TEXT PRIMARY KEY, make TEXT, model TEXT, price REAL, 
                  first_seen TEXT, last_seen TEXT, status TEXT)''')
    return conn

def scrape(url, label):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0 Safari/537.36"}
    try:
        time.sleep(random.uniform(5, 8))
        res = requests.get(url, headers=headers, timeout=30)
        if res.status_code != 200: return []
        soup = BeautifulSoup(res.text, "html.parser")
        items = []
        for art in soup.find_all("article", {"data-ad-id": True}):
            p_tag = art.find("span", {"data-testid": "price-label"})
            if p_tag:
                price = int(''.join(filter(str.isdigit, p_tag.get_text())))
                items.append((art.get("data-ad-id"), price))
        return items
    except:
        return []

def main():
    targets = [
        {"id": "D1", "url": "https://suchen.mobile.de/fahrzeuge/search.html?isSearchRequest=true&od=down&ref=followDealerPage&s=Car&sb=doc&sid=494668&vc=Car"},
        {"id": "D2", "url": "https://suchen.mobile.de/fahrzeuge/search.html?isSearchRequest=true&od=down&ref=followDealerPage&s=Car&sb=doc&sid=14520262&vc=Car"}
    ]
    
    conn = get_db()
    today = date.today().isoformat()
    
    for t in targets:
        print(f"Scraping {t['id']}...")
        data = scrape(t['url'], t['id'])
        for ad_id, price in data:
            conn.execute('''INSERT INTO cars VALUES (?,?,?,?,?,?,?) 
                         ON CONFLICT(ad_id) DO UPDATE SET last_seen=?, price=?, status='active' ''',
                         (ad_id, "Dealer", t['id'], price, today, today, 'active', today, price))
        conn.commit()
    conn.close()
    print("Gata!")

if __name__ == "__main__":
    main()

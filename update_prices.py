import sqlite3
import os
import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import date

# Configurare
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "cars.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Conectare DB
conn = sqlite3.connect(DB_PATH)
conn.execute('''CREATE TABLE IF NOT EXISTS cars 
             (ad_id TEXT PRIMARY KEY, make TEXT, model TEXT, price REAL, 
              first_seen TEXT, last_seen TEXT, status TEXT)''')

targets = [
    {"id": "Dealer_1", "url": "https://suchen.mobile.de/fahrzeuge/search.html?isSearchRequest=true&od=down&ref=followDealerPage&s=Car&sb=doc&sid=494668&vc=Car"},
    {"id": "Dealer_2", "url": "https://suchen.mobile.de/fahrzeuge/search.html?isSearchRequest=true&od=down&ref=followDealerPage&s=Car&sb=doc&sid=14520262&vc=Car"}
]

today = date.today().isoformat()
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0"}

print(f"Incepe scanarea: {today}")

for t in targets:
    print(f"Scanam {t['id']}...")
    time.sleep(random.uniform(5, 8))
    try:
        res = requests.get(t['url'], headers=headers, timeout=30)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            articles = soup.find_all("article", {"data-ad-id": True})
            for art in articles:
                ad_id = art.get("data-ad-id")
                p_tag = art.find("span", {"data-testid": "price-label"})
                if ad_id and p_tag:
                    price = int(''.join(filter(str.isdigit, p_tag.get_text())))
                    conn.execute('''INSERT INTO cars VALUES (?,?,?,?,?,?,?) 
                                 ON CONFLICT(ad_id) DO UPDATE SET 
                                 price=excluded.price, last_seen=excluded.last_seen, status='active' ''',
                                 (ad_id, "Dealer", t['id'], price, today, today, 'active'))
            conn.commit()
            print(f"Gata pentru {t['id']}")
        else:
            print(f"Eroare HTTP {res.status_code}")
    except Exception as e:
        print(f"Eroare: {e}")

conn.close()
print("Proces complet!")

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

conn = sqlite3.connect(DB_PATH)
conn.execute('''CREATE TABLE IF NOT EXISTS cars 
             (ad_id TEXT PRIMARY KEY, make TEXT, model TEXT, price REAL, 
              first_seen TEXT, last_seen TEXT, status TEXT)''')

targets = [
    {"id": "Dealer_1", "url": "https://suchen.mobile.de/fahrzeuge/search.html?isSearchRequest=true&od=down&ref=followDealerPage&s=Car&sb=doc&sid=494668&vc=Car"},
    {"id": "Dealer_2", "url": "https://suchen.mobile.de/fahrzeuge/search.html?isSearchRequest=true&od=down&ref=followDealerPage&s=Car&sb=doc&sid=14520262&vc=Car"}
]

today = date.today().isoformat()

# Header-e mult mai complexe
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,ro;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0"
}

print(f"Incepe scanarea: {today}")

# Folosim o sesiune pentru a pastra cookie-urile
session = requests.Session()
session.headers.update(headers)

for t in targets:
    print(f"Scanam {t['id']}...")
    # Pauza mai mare intre dealeri
    time.sleep(random.uniform(10, 20))
    
    try:
        # Prima data accesam homepage-ul pentru a lua un cookie "curat"
        session.get("https://www.mobile.de", timeout=20)
        time.sleep(2)
        
        res = session.get(t['url'], timeout=30)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            articles = soup.find_all("article", {"data-ad-id": True})
            count = 0
            for art in articles:
                ad_id = art.get("data-ad-id")
                p_tag = art.find("span", {"data-testid": "price-label"})
                if ad_id and p_tag:
                    price = int(''.join(filter(str.isdigit, p_tag.get_text())))
                    conn.execute('''INSERT INTO cars VALUES (?,?,?,?,?,?,?) 
                                 ON CONFLICT(ad_id) DO UPDATE SET 
                                 price=excluded.price, last_seen=excluded.last_seen, status='active' ''',
                                 (ad_id, "Dealer", t['id'], price, today, today, 'active'))
                    count += 1
            conn.commit()
            print(f"Succes: am gasit {count} masini pentru {t['id']}")
        else:
            print(f"Eroare HTTP {res.status_code} - Mobile.de inca blocheaza accesul.")
            
    except Exception as e:
        print(f"Eroare: {e}")

conn.close()
print("Proces complet!")

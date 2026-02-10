import sqlite3
import os
import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import date

# 1. Configurare Căi
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DB_DIR, "cars.db")

if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

# 2. Conectare Bază de Date și Creare Tabel
conn = sqlite3.connect(DB_PATH)
conn.execute('''CREATE TABLE IF NOT EXISTS cars 
             (ad_id TEXT PRIMARY KEY, make TEXT, model TEXT, price REAL, 
              first_seen TEXT, last_seen TEXT, status TEXT)''')

# 3. Configurare Target-uri
targets = [
    {"id": "Dealer_1", "url": "https://suchen.mobile.de/fahrzeuge/search.html?isSearchRequest=true&od=down&ref=followDealerPage&s=Car&sb=doc&sid=494668&vc=Car"},
    {"id": "Dealer_2", "url": "https://suchen.mobile.de/fahrzeuge/search.html?isSearchRequest=true&od=down&ref=followDealerPage&s=Car&sb=doc&sid=14520262&vc=Car"}
]

today = date.today().isoformat()
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0"}

# 4. Bucla Principală de Scraping
print(f"--- Start Scraping: {today} ---")

for t in targets:
    print(f"Accesare {t['id']}...")
    time.sleep(random.uniform(5, 8))
    
    try:
        res = requests.get(t['url'], headers=headers, timeout=30)
        if res.status_code != 200:
            print(f"Eroare HTTP {res.status_code} la {t['id']}")
            continue
            
        soup = BeautifulSoup(res.text, "html.parser")
        articles = soup.find_all("article", {"data-ad-id": True})
        
        count = 0
        for art in articles:
            ad_id = art.get("data-ad-id")
            p_tag = art.find("span", {"data-testid": "price-label"})
            
            if ad_id and p_tag:
                price_text = p_tag.get_text()
                price = int(''.join(filter(str.isdigit, price_text)))
                
                # UPSERT (Insert sau Update)
                conn.execute('''
                    INSERT INTO cars (ad_id, make, model, price, first_seen, last_seen, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(ad_id) DO UPDATE SET 
                        price = excluded.price,
                        last_seen = excluded.last_seen,
                        status = 'active'
                ''', (ad_id, "Dealer", t['id'], price, today, today, 'active'))
                count += 1
        
        conn.commit()
        print(f"Succes: {count} anunțuri salvate pentru {t['id']}")
            
    except Exception as e:
        print(f"Eroare critică la {t['id']}: {e}")

conn.close()
print("Proces finalizat.")

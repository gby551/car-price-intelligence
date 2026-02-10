import sqlite3
import os
import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import date

# 1. Configurare Căi
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "cars.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# 2. Configurare Linkuri
targets = [
    {"id": "Dealer_1", "url": "https://suchen.mobile.de/fahrzeuge/search.html?isSearchRequest=true&od=down&ref=followDealerPage&s=Car&sb=doc&sid=494668&vc=Car"},
    {"id": "Dealer_2", "url": "https://suchen.mobile.de/fahrzeuge/search.html?isSearchRequest=true&od=down&ref=followDealerPage&s=Car&sb=doc&sid=14520262&vc=Car"}
]

def run_scraper():
    conn = sqlite3.connect(DB_PATH)
    # Creăm tabelul dacă nu există
    conn.execute('''CREATE TABLE IF NOT EXISTS cars 
                 (ad_id TEXT PRIMARY KEY, make TEXT, model TEXT, price REAL, 
                  first_seen TEXT, last_seen TEXT, status TEXT)''')
    
    today = date.today().isoformat()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0"}

    for t in targets:
        print(f"Accesare {t['id']}...")
        time.sleep(random.uniform(5, 8))
        
        try:
            res = requests.get(t['url'], headers=headers, timeout=30)
            if res.status_code != 200:
                print(f"Eroare HTTP {res.status_code}")
                continue
                
            soup = BeautifulSoup(res.text, "html.parser")
            articles = soup.find_all("article", {"data-ad-id": True})
            
            for art in articles:
                ad_id = art.get("data-ad-id")
                p_tag = art.find("span", {"data-testid": "price-label"})
                
                if ad_id and p_tag:
                    price = int(''.join(filter(str.isdigit, p_tag.get_text())))
                    
                    # Logica de salvare (Insert sau Update dacă există deja)
                    conn.execute('''
                        INSERT INTO cars (ad_id, make, model, price, first_seen, last_seen, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(ad_id) DO UPDATE SET 
                            price = excluded.price,
                            last_seen = excluded.last_seen,
                            status = 'active'
                    ''', (ad_id, "Dealer", t['id'], price, today, today, 'active'))
            
            conn.commit()
            print(f"Succes pentru {t['id']}")
            
        except Exception as e:
            print(f"Eroare la {t['id']}: {e}")

    conn.close()

if __name__ == "__main__":
    run_scraper()

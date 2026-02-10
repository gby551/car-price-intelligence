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

# Am schimbat link-urile pe varianta de RO, uneori ajuta la 403
targets = [
    {"id": "Dealer_1", "url": "https://www.mobile.de/ro/automobil/haendler/autohaus-mayer-e.k.-gross-gerau-id494668.html"},
    {"id": "Dealer_2", "url": "https://www.mobile.de/ro/automobil/haendler/auto-park-rath-id14520262.html"}
]

today = date.today().isoformat()

def get_data(url):
    # Incercam sa parem cat mai umani posibil
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ]
    
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.com/",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    try:
        # Pauza mare: Mobile.de detecteaza viteza
        time.sleep(random.uniform(15, 25))
        response = requests.get(url, headers=headers, timeout=30)
        return response
    except Exception as e:
        print(f"Eroare conexiune: {e}")
        return None

print(f"Incepe scanarea: {today}")

for t in targets:
    print(f"Scanam {t['id']}...")
    res = get_data(t['url'])
    
    if res and res.status_code == 200:
        soup = BeautifulSoup(res.text, "html.parser")
        # Nota: Mobile.de RO s-ar putea sa aiba clase diferite. 
        # Cautam ID-ul de anunt care e standard
        articles = soup.find_all("article", {"data-ad-id": True})
        
        count = 0
        for art in articles:
            ad_id = art.get("data-ad-id")
            # Cautam orice tag care contine pretul
            price_box = art.find(lambda tag: tag.name == 'span' and 'price' in tag.get('data-testid', '').lower())
            
            if ad_id and price_box:
                price = int(''.join(filter(str.isdigit, price_box.get_text())))
                conn.execute('''INSERT INTO cars VALUES (?,?,?,?,?,?,?) 
                             ON CONFLICT(ad_id) DO UPDATE SET 
                             price=excluded.price, last_seen=excluded.last_seen, status='active'''',
                             (ad_id, "Dealer", t['id'], price, today, today, 'active'))
                count += 1
        
        conn.commit()
        print(f"Succes: {count} masini gasite.")
    elif res:
        print(f"Eroare HTTP {res.status_code}. Mobile.de ne-a refuzat.")
    else:
        print("Nu s-a primit raspuns.")

conn.close()
print("Proces complet.")

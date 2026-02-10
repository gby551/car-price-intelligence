import sqlite3
import pandas as pd
from datetime import date
import requests
from bs4 import BeautifulSoup
import time
import random
import os
import sys

# Setăm căile pentru a funcționa corect pe GitHub Actions
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DB_DIR, "cars.db")

def get_db_connection():
    try:
        if not os.path.exists(DB_DIR):
            os.makedirs(DB_DIR)
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Structura tabelului pentru tracking individual
        c.execute('''CREATE TABLE IF NOT EXISTS cars (
            ad_id TEXT PRIMARY KEY, 
            make TEXT, 
            model TEXT, 
            price REAL, 
            first_seen TEXT, 
            last_seen TEXT, 
            status TEXT DEFAULT 'active')''')
        conn.commit()
        return conn
    except Exception as e:
        print(f"EROARE DATABASE: {e}")
        sys.exit(1)

def scrape_mobile_page(url, label):
    # User-Agent-ul este critic pentru a evita blocarea instantanee
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "en-GB,en;q=0.9,ro-RO;q=0.8,ro;q=0.7",
        "Referer": "https://www.google.com"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code != 200:
            print(f"Eroare HTTP {response.status_code} la link-ul: {label}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        listings = []
        
        # Mobile.de folosește 'article' cu un atribut 'data-ad-id' pentru fiecare anunț
        articles = soup.find_all("article", {"data-ad-id": True})
        
        for article in articles:
            ad_id = article.get("data-ad-id")
            
            # Căutăm prețul - Mobile.de folosește adesea clase care conțin 'price' sau 'price-label'
            price_tag = article.find("span", {"data-testid": "price-label"})
            
            if ad_id and price_tag:
                # Curățăm prețul (eliminăm €, puncte, spații)
                price_text = price_tag.get_text()
                price = int(''.join(filter(str.isdigit, price_text)))
                
                # Deoarece link-urile sunt de dealer, nu știm brand-ul din URL
                # Îl lăsăm 'Generic/Dealer' sau poți să îl schimbi tu
                listings.append({
                    "ad_id": ad_id, 
                    "price": price,
                    "make": "Dealer_Car", # Poți rafina asta dacă vrei
                    "model": label
                })
        
        return listings
    except Exception as e:
        print(f"Eroare la scraping {label}: {e}")
        return []

def update_database(listings):
    if not listings:
        return
    
    conn = get_db_connection()
    c = conn.cursor()
    today = date.today().isoformat()
    
    # Colectăm ID-urile procesate în această rulare
    all_current_ids = [item['ad_id'] for item in listings]

    for item in listings:
        # Vedem dacă mașina există deja
        c.execute("SELECT price FROM cars WHERE ad_id = ?", (item['ad_id'],))
        row = c.fetchone()

        if row:
            # Update preț și data ultimei vizualizări
            c.execute("""
                UPDATE cars 
                SET last_seen = ?, price = ?, status = 'active' 
                WHERE ad_id = ?
            """, (today, item['price'], item['ad_id']))
        else:
            # Insert mașină nouă
            c.execute("""
                INSERT INTO cars (ad_id, make, model, price, first_seen, last_seen, status)
                VALUES (?, ?, ?, ?, ?, ?, 'active')
            """, (item['ad_id'], item['make'], item['model'], item['price'], today, today, 'active'))

    # Logica de "Vândut": dacă era activă ieri dar nu a fost găsită azi, e 'sold'
    # ATENȚIE: Aceasta funcționează doar pentru modelele scanate azi
    distinct_models = set(item['model'] for item in listings)
    for model_name in distinct_models:
        placeholders = ', '.join(['?'] * len(all_current_ids))
        query = f"""
            UPDATE cars 
            SET status = 'sold' 
            WHERE model = ? 
            AND status = 'active' 
            AND ad_id NOT IN ({placeholders})
            AND last_seen < ?
        """
        c.execute(query, (model_name, *all_current_ids, today))
    
    conn.commit()
    conn.close()

def main():
    target_links = [
        {
            "label": "Dealer_1_Sid_494668",
            "url": "https://suchen.mobile.de/fahrzeuge/search.html?isSearchRequest=true&od=down&ref=followDealerPage&s=Car&sb=doc&sid=494668&vc=Car"
        },
        {
            "label": "Dealer_2_Sid_14520262",
            "url": "https://suchen.mobile.de/fahrzeuge/search.html?isSearchRequest=true&od=down&ref=followDealerPage&s=Car&sb=doc&sid=14520262&vc=Car"
        }
    ]

    print(f"--- START SCRAPE: {date.today().isoformat()} ---")
    
    all_found_data = []
    for target in target_links:
        print(f"Procesare: {target['label']}...")
        data = scrape_mobile_page(target['url'], target['label'])
        if data:
            print(f"Am găsit {len(data)} anunțuri.")
            all_found_data.extend(data)
        else:
            print(f"Niciun anunț găsit pentru {target['label']}. Verifică blocaj IP.")
        
        # Așteptăm între 5 și 10 secunde ca să nu fim blocați
        time.sleep(random.uniform(5, 10))

    if all_found_data:
        update_database(all_found_data)
        print("Baza de date a fost actualizată cu succes.")
    else:
        print("Nu s-au găsit date noi. Nimic de salvat.")

if __name__ == "__main__":
    main()

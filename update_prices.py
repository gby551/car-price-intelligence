import sqlite3
import pandas as pd
from datetime import date
import requests
from bs4 import BeautifulSoup
import time
import random
import os
import sys

# Calculăm calea absolută pentru a evita erorile pe Linux/GitHub
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DB_DIR, "cars.db")

def get_db_connection():
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS cars (
        ad_id TEXT PRIMARY KEY, make TEXT, model TEXT, price REAL, 
        first_seen TEXT, last_seen TEXT, status TEXT DEFAULT 'active')''')
    conn.commit()
    return conn

def scrape_dealer(url, label):
    # Simulăm un browser real de pe un Mac
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }
    
    # Adăugăm un delay generos și aleatoriu
    time.sleep(random.uniform(5, 12))
    
    try:
        # Folosim un Session pentru a păstra Cookie-urile
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=30)
        
        if response.status_code == 403:
            print(f"Bust! 403 Forbidden pentru {label}. Mobile.de ne-a blocat.")
            return []
            
        # ... restul codului de parsing (BeautifulSoup) rămâne la fel

def main():
    target_links = [
        {"label": "Dealer_494668", "url": "https://suchen.mobile.de/fahrzeuge/search.html?isSearchRequest=true&od=down&ref=followDealerPage&s=Car&sb=doc&sid=494668&vc=Car"},
        {"label": "Dealer_14520262", "url": "https://suchen.mobile.de/fahrzeuge/search.html?isSearchRequest=true&od=down&ref=followDealerPage&s=Car&sb=doc&sid=14520262&vc=Car"}
    ]

    conn = get_db_connection()
    c = conn.cursor()
    today = date.today().isoformat()
    
    for target in target_links:
        print(f"Scraping {target['label']}...")
        listings = scrape_dealer(target['url'], target['label'])
        
        if not listings:
            continue

        found_ids = [l['ad_id'] for l in listings]

        for item in listings:
            c.execute("SELECT price FROM cars WHERE ad_id = ?", (item['ad_id'],))
            if c.fetchone():
                c.execute("UPDATE cars SET last_seen = ?, price = ?, status = 'active' WHERE ad_id = ?", 
                          (today, item['price'], item['ad_id']))
            else:
                c.execute("INSERT INTO cars (ad_id, make, model, price, first_seen, last_seen, status) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                          (item['ad_id'], "Dealer", target['label'], item['price'], today, today, 'active'))

        # Marcăm ca vândute mașinile care au dispărut de la acest dealer
        placeholders = ', '.join(['?'] * len(found_ids))
        c.execute(f"UPDATE cars SET status = 'sold' WHERE model = ? AND status = 'active' AND ad_id NOT IN ({placeholders})", 
                  (target['label'], *found_ids))
        
        print(f"Am găsit {len(listings)} mașini.")

    conn.commit()
    conn.close()
    print("Update terminat cu succes.")

if __name__ == "__main__":
    main()

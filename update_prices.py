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
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        # Adăugăm un mic delay să nu fim blocați de la prima cerere
        time.sleep(random.uniform(2, 4))
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code != 200:
            print(f"Eroare {response.status_code} la {label}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        listings = []
        # Mobile.de listări
        articles = soup.find_all("article", {"data-ad-id": True})
        
        for article in articles:
            ad_id = article.get("data-ad-id")
            price_tag = article.find("span", {"data-testid": "price-label"})
            if ad_id and price_tag:
                price = int(''.join(filter(str.isdigit, price_tag.get_text())))
                listings.append({"ad_id": ad_id, "price": price})
        return listings
    except Exception as e:
        print(f"Eroare scraping {label}: {e}")
        return []

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

import sqlite3
import pandas as pd
from datetime import date
import requests
from bs4 import BeautifulSoup
import time
import random
import os

DB_DIR = "database"
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

def scrape_custom_url(url, make, model):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.com"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Eroare {response.status_code} pentru {make}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        listings = []
        
        # Căutăm containerele de anunțuri
        articles = soup.find_all("article", {"data-testid": "result-listing"})
        
        for article in articles:
            ad_id = article.get("data-ad-id")
            price_tag = article.find("span", {"data-testid": "price-label"})
            if price_tag and ad_id:
                price_text = price_tag.get_text()
                price = int(''.join(filter(str.isdigit, price_text)))
                listings.append({"ad_id": ad_id, "price": price})
        return listings
    except Exception as e:
        print(f"Eroare la {make}: {e}")
        return []

def update_database(make, model, listings):
    conn = get_db_connection()
    c = conn.cursor()
    today = date.today().isoformat()
    found_ids = [item['ad_id'] for item in listings]

    for item in listings:
        c.execute("SELECT price FROM cars WHERE ad_id = ?", (item['ad_id'],))
        if c.fetchone():
            c.execute("UPDATE cars SET last_seen = ?, price = ?, status = 'active' WHERE ad_id = ?", 
                      (today, item['price'], item['ad_id']))
        else:
            c.execute("INSERT INTO cars VALUES (?, ?, ?, ?, ?, ?, 'active')", 
                      (item['ad_id'], make, model, item['price'], today, today))

    # Marcăm ca vândute mașinile care nu mai apar în acest set de rezultate
    c.execute(f"UPDATE cars SET status = 'sold' WHERE make = ? AND model = ? AND status = 'active' AND ad_id NOT IN ({','.join(['?']*len(found_ids))})", 
              (make, model, *found_ids))
    conn.commit()
    conn.close()

def main():
    # AICI pui cele 2 linkuri de pe Mobile.de
    # Sfat: Folosește link-uri care au deja filtrele de preț/an aplicate
    target_links = [
        {
            "make": "VW", 
            "model": "Golf 8", 
            "url": "https://suchen.mobile.de/fahrzeuge/search.html?isSearchRequest=true&od=down&ref=followDealerPage&s=Car&sb=doc&sid=494668&vc=Car"
        },
        {
            "make": "BMW", 
            "model": "Seria 3", 
            "url": "https://suchen.mobile.de/fahrzeuge/search.html?isSearchRequest=true&od=down&ref=followDealerPage&s=Car&sb=doc&sid=14520262&vc=Car"
        }
    ]

    for target in target_links:
        print(f"Scraping {target['make']} {target['model']}...")
        data = scrape_custom_url(target['url'], target['make'], target['model'])
        if data:
            update_database(target['make'], target['model'], data)
            print(f"Am găsit {len(data)} anunțuri.")
        time.sleep(random.uniform(5, 10))

if __name__ == "__main__":
    main()

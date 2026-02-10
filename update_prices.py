import sqlite3
import pandas as pd
from datetime import date
import requests
from bs4 import BeautifulSoup
import time
import random
import os
import sys

# Căi absolute pentru a evita erorile pe mediul Linux GitHub
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
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": "https://www.google.com"
    }
    try:
        # Pauză strategică pentru a evita detectarea ca bot
        time.sleep(random.uniform(5, 10))
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"Eroare {response.status_code} la {label}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        listings = []
        articles = soup.find_all("article", {"data-ad-id": True})
        
        for article in articles:
            ad_id = article.get("data-ad-id")
            price_tag = article.find("span", {"data-testid": "price-label"})
            if ad_id and price_tag:
                price_text = price_tag.get_text()
                price = int(''.join(filter(str.isdigit, price_text)))
                listings.append({"ad_id": ad_id, "price": price})
        return listings
    except Exception as e:
        print(f"Eroare la scraping {label}: {e}")
        return []

def update_database(make, model, listings):
    if not listings:
        return
    conn = get_db_connection()
    c = conn.cursor()
    today = date.today().isoformat()
    found_ids = [l['ad_id'] for l in listings]

    for item in listings:
        c.execute("SELECT price FROM cars WHERE ad_id = ?", (item['ad_id'],))
        if c.fetchone():
            c.execute("UPDATE cars SET last_seen = ?, price = ?, status = 'active' WHERE ad_id = ?", 
                      (today, item['price'], item['ad_id']))
        else:
            c.execute("INSERT INTO cars (ad_id, make, model, price, first_seen, last_seen, status) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                      (item['ad_id'], make, model, item['price'], today, today, 'active'))

    # Marcăm mașinile care nu mai sunt în link-uri ca fiind 'sold'
    placeholders = ', '.join(['?'] * len(found_ids))
    c.execute(f"UPDATE cars SET status = 'sold' WHERE model = ? AND status = 'active' AND ad_id NOT IN ({placeholders})", 
              (model, *found_ids))
    conn.commit()
    conn.close()

def main():
    target_links = [
        {"label": "Dealer_494668", "url": "https://suchen.mobile.de/fahrzeuge/search.html?isSearchRequest=true&od=down&ref=followDealerPage&s=Car&sb=doc&sid=494668&vc=Car"},
        {"label": "Dealer_14520262", "url": "https://suchen.mobile.de/fahrzeuge/search.html?isSearchRequest=true&od=down&ref=followDealerPage&s=Car&sb=doc&sid=14520262&vc=Car"}
    ]

    print(f"--- Start Scraping: {date.today()} ---")
    for target in target_links:
        print(f"Procesare {target['label']}...")
        data = scrape_dealer(target['url'], target['label'])
        if data:
            update_database("Dealer", target['label'], data)
            print(f"Succes: {len(data)} anunțuri găsite.")
        else:
            print(f"Nu s-au extras date pentru {target['label']}.")

if __name__ == "__main__":
    main()

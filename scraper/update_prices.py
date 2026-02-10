import sqlite3
import pandas as pd
from datetime import date
import requests
from bs4 import BeautifulSoup
import time
import random

DB_PATH = "cars.db"

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }

def scrape_page(url):
    try:
        # Notă: În producție, aici vei avea nevoie de un proxy sau undetected-chromedriver
        response = requests.get(url, headers=get_headers(), timeout=15)
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.text, "html.parser")
        listings = []
        
        # Selector generic (trebuie verificat periodic pe site)
        # Mobile.de își schimbă des clasele CSS (ex: .cnd-item sau data-testid)
        for item in soup.select('a[data-testid="result-listing"]'):
            ad_id = item.get('data-ad-id')
            price_text = item.select_one('[data-testid="price-label"]').get_text()
            price = int(''.join(filter(str.isdigit, price_text)))
            
            listings.append({
                'id': ad_id,
                'price': price,
                'last_seen': date.today().isoformat()
            })
        return listings
    except Exception as e:
        print(f"Eroare: {e}")
        return []

def update_database(listings, make, model):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Marcăm toate mașinile acestui model ca fiind potențial "dispărute"
    # Dacă le găsim în scrape, le vom reactiva
    
    today = date.today().isoformat()
    
    for car in listings:
        # Verificăm dacă există deja
        c.execute("SELECT price FROM cars WHERE ad_id = ?", (car['id'],))
        row = f.fetchone()
        
        if row:
            old_price = row[0]
            # Update preț și data ultimei vizualizări
            c.execute("""
                UPDATE cars SET price = ?, last_seen = ?, status = 'active' 
                WHERE ad_id = ?
            """, (car['price'], today, car['id']))
        else:
            # Insert mașină nouă
            c.execute("""
                INSERT INTO cars (ad_id, make, model, price, first_seen, last_seen, status)
                VALUES (?, ?, ?, ?, ?, ?, 'active')
            """, (car['id'], make, model, car['price'], today, today))
            
    # 2. Logică pentru vânzare:
    # Orice mașină care era 'active' ieri, dar NU a fost găsită azi, o marcăm ca 'sold'
    c.execute("""
        UPDATE cars SET status = 'sold' 
        WHERE make = ? AND model = ? AND last_seen < ? AND status = 'active'
    """, (make, model, today))
    
    conn.commit()
    conn.close()

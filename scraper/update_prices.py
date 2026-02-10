import sqlite3
import pandas as pd
from datetime import date
import requests
from bs4 import BeautifulSoup
import time
import random
import os

# Configurare poteci
DB_DIR = "database"
DB_PATH = os.path.join(DB_DIR, "cars.db")

def get_db_connection():
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Tabel principal pentru starea actuală a anunțurilor
    c.execute('''
        CREATE TABLE IF NOT EXISTS cars (
            ad_id TEXT PRIMARY KEY,
            make TEXT,
            model TEXT,
            price REAL,
            first_seen TEXT,
            last_seen TEXT,
            status TEXT DEFAULT 'active'
        )
    ''')
    # Tabel pentru istoricul modificărilor de preț
    c.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            ad_id TEXT,
            price REAL,
            date TEXT
        )
    ''')
    conn.commit()
    return conn

def scrape_mobile_de(make, model):
    """
    Simulează extragerea datelor. 
    NOTĂ: Mobile.de necesită headere de browser reale și uneori proxy-uri.
    """
    # Înlocuiește cu ID-urile reale din URL-ul Mobile.de după o căutare manuală
    # Exemplu: Volkswagen = 25200, Golf = 14
    url = f"https://www.mobile.de/ro/automobil/{{make}}-{{model}}/vhc:car"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    try:
        # Folosim un timeout generos
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Eroare HTTP {response.status_code} pentru {make} {model}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        listings = []

        # Selectorii de mai jos sunt generici; Mobile.de își schimbă clasele des.
        # Adesea folosesc atribute tip 'data-testid="result-listing"'
        articles = soup.find_all("article", {"data-testid": "result-listing"})

        for article in articles:
            ad_id = article.get("data-ad-id")
            # Extragere preț (curățare caractere non-numerice)
            price_tag = article.find("span", {"data-testid": "price-label"})
            if price_tag and ad_id:
                price_text = price_tag.get_text()
                price = int(''.join(filter(str.isdigit, price_text)))
                listings.append({
                    "ad_id": ad_id,
                    "price": price
                })
        
        return listings

    except Exception as e:
        print(f"Eroare la scraping pentru {make} {model}: {e}")
        return []

def update_database(make, model, listings):
    conn = get_db_connection()
    c = conn.cursor()
    today = date.today().isoformat()
    
    found_ids = []

    for item in listings:
        ad_id = item['ad_id']
        price = item['price']
        found_ids.append(ad_id)

        # Verificăm dacă anunțul există deja
        c.execute("SELECT price FROM cars WHERE ad_id = ?", (ad_id,))
        row = c.fetchone()

        if row:
            old_price = row[0]
            # Dacă prețul s-a schimbat, salvăm în istoric
            if old_price != price:
                c.execute("INSERT INTO price_history (ad_id, price, date) VALUES (?, ?, ?)", 
                          (ad_id, price, today))
            
            # Actualizăm data ultimei vizualizări și prețul curent
            c.execute("UPDATE cars SET last_seen = ?, price = ?, status = 'active' WHERE ad_id = ?", 
                      (today, price, ad_id))
        else:
            # Anunț nou detectat
            c.execute("""
                INSERT INTO cars (ad_id, make, model, price, first_seen, last_seen, status)
                VALUES (?, ?, ?, ?, ?, ?, 'active')
            """, (ad_id, make, model, price, today, today))

    # Logica pentru vânzare: Dacă o mașină era 'active' dar nu a apărut în scrape-ul de azi
    # O marcăm ca 'sold'. Atenție: funcționează corect doar dacă scraping-ul a parcurs TOATE paginile.
    if found_ids:
        placeholders = ', '.join(['?'] * len(found_ids))
        c.execute(f"""
            UPDATE cars 
            SET status = 'sold' 
            WHERE make = ? AND model = ? 
            AND status = 'active' 
            AND ad_id NOT IN ({placeholders})
        """, (make, model, *found_ids))

    conn.commit()
    conn.close()

def main():
    # Definește aici ce mașini vrei să urmărești
    # Ideal, acestea ar trebui să vină dintr-un fișier de configurare sau din DB
    target_cars = [
        {"make": "volkswagen", "model": "golf"},
        {"make": "bmw", "model": "3er"},
        {"make": "audi", "model": "a4"}
    ]

    print(f"--- Start Update: {date.today()} ---")

    for car in target_cars:
        print(f"Scraping {car['make']} {car['model']}...")
        listings = scrape_mobile_de(car['make'], car['model'])
        
        if listings:
            update_database(car['make'], car['model'], listings)
            print(f"Succes: Am găsit {len(listings)} anunțuri.")
        else:
            print(f"Atenție: Nu s-au extras date pentru {car['make']}.")
        
        # Delay random pentru a nu fi detectat ca bot
        time.sleep(random.uniform(5, 10))

    print("--- Update Complet ---")

if __name__ == "__main__":
    main()

import sqlite3
import pandas as pd
from datetime import date
import requests
from bs4 import BeautifulSoup
import time
import random
import os

DB_PATH = "../database/cars.db"

def scrape_mobile_de(make, model):
    make_clean = make.lower().replace(" ", "-")
    model_clean = model.lower().replace(" ", "-")
    
    # URL generic de căutare (trebuie adaptat la structura reală Mobile.de)
    url = f"https://www.mobile.de/de/suche/?damaged=false&isSearchRequest=true&makeModelVariant1.makeId={make_clean}&makeModelVariant1.modelId={model_clean}"
    
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        price_tag = soup.select_one(".adPrice")  # exemplu generic
        if not price_tag:
            return None

        price_str = price_tag.get_text()
        price = int(price_str.replace("€","").replace(".","").replace(",","").strip())
        return price
    except Exception as e:
        print(f"Error scraping {make} {model}: {e}")
        return None

def update_prices():
    if not os.path.exists(DB_PATH):
        print("Baza de date nu există. Creează întâi dashboard-ul pentru a genera DB.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    df = pd.read_sql_query("SELECT DISTINCT make, model FROM cars", conn)
    today = date.today().isoformat()

    for _, row in df.iterrows():
        make = row['make']
        model = row['model']
        price = scrape_mobile_de(make, model)
        if price:
            c.execute("""
                INSERT INTO cars (make, model, year, mileage, price, date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (make, model, 0, 0, price, today))
            print(f"{make} {model} → {price}€")
        else:
            print(f"{make} {model} → preț nu găsit")
        time.sleep(random.uniform(1,2))  # evită blocarea IP

    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_prices()

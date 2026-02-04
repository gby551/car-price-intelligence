import sqlite3
import pandas as pd
from datetime import date
import requests
from bs4 import BeautifulSoup
import time
import random

DB_PATH = "../database/cars.db"

def scrape_mobile_de(make, model):
    """
    Caută prețul unei mașini pe Mobile.de.
    Returnează primul preț găsit (int) sau None dacă nu găsește.
    """
    # Pregătim make și model pentru URL (minus diacritice, lowercase, spații -> '-')
    make_clean = make.lower().replace(" ", "-")
    model_clean = model.lower().replace(" ", "-")

    # URL de căutare - exemplu generic (poate fi ajustat după structura reală Mobile.de)
    url = f"https://www.mobile.de/de/suche/?damaged=false&isSearchRequest=true&makeModelVariant1.makeId={make_clean}&makeModelVariant1.modelId={model_clean}"

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Selector generic pentru primul preț (exemplu)
        price_tag = soup.select_one(".adPrice")
        if not price_tag:
            return None

        price_str = price_tag.get_text()
        # Curățare șir
        price = int(price_str.replace("€", "").replace(".", "").replace(",", "").strip())
        return price

    except Exception as e:
        print(f"Error scraping {make} {model}: {e}")
        return None

def update_prices():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Preluăm toate mașinile favorite
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
            print(f"Updated {make} {model} with price {price} for {today}")
        else:
            print(f"No price found for {make} {model}")

        # Pauză random între request-uri ca să nu fie blocat
        time.sleep(random.uniform(1, 3))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_prices()

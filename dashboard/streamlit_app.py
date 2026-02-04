"""
Streamlit Dashboard - Car Price Intelligence

Dashboard privat, accesibil de oriunde
UI în română

TAB-uri:
1. Evoluție Prețuri Mobile.de
2. Mașini Similare RO
3. Rezumat Zilnic

Funcționalități reale se vor implementa ulterior în locul placeholder-elor.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

# ---------- CONFIGURARE PAGINĂ ----------
st.set_page_config(page_title="Car Price Intelligence", layout="wide")

# ---------- TAB-URI ----------
tab1, tab2, tab3 = st.tabs([
    "📉 Evoluție Prețuri",
    "🔎 Mașini Similare RO",
    "📬 Rezumat Zilnic"
])
# ---------------- PASSWORD PROTECTION ----------------
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["DASHBOARD_PASSWORD"]:
            st.session_state["authenticated"] = True
        else:
            st.session_state["authenticated"] = False

    if "authenticated" not in st.session_state:
        st.text_input("Introdu parola:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["authenticated"]:
        st.text_input("Introdu parola:", type="password", on_change=password_entered, key="password")
        st.error("Parola greșită")
        return False
    else:
        return True

if not check_password():
    st.stop()
# ---------------- PASSWORD PROTECTION END ----------------

# ---------- TAB 1: Evoluție Prețuri ----------
with tab1:
    st.header("Evoluție Prețuri Mobile.de")
    st.write("Aici vor fi afișate graficele și tabelele cu istoricul prețurilor pentru mașinile tale favorite.")
    
    # Placeholder tabel
    df_placeholder = pd.DataFrame({
        "Mașină": ["BMW 530d", "Audi A6"],
        "Preț actual (€)": [32000, 29000],
        "Preț inițial (€)": [33000, 29500],
        "Diferență (€)": [-1000, -500]
    })
    st.table(df_placeholder)

    # Placeholder grafic evoluție preț
    df_graph = pd.DataFrame({
        "Data": pd.date_range(start="2026-01-01", periods=5, freq='D'),
        "BMW 530d": [33000, 32800, 32500, 32200, 32000],
        "Audi A6": [29500, 29400, 29300, 29100, 29000]
    })
    fig = px.line(df_graph, x="Data", y=["BMW 530d", "Audi A6"], title="Evoluție Prețuri")
    st.plotly_chart(fig, use_container_width=True)

# ---------- TAB 2: Mașini Similare RO ----------
with tab2:
    st.header("Mașini Similare RO (OLX + Autovit)")
    st.write("Top 10 mașini cele mai apropiate ca specificații pentru fiecare favorit bifat.")

    # Placeholder dropdown pentru selectarea mașinii favorite
    masina_selectata = st.selectbox("Selectează o mașină din Watchlist", df_placeholder["Mașină"])

    # Placeholder tabel top 10 similare
    df_similar = pd.DataFrame({
        "Scor Similaritate": [95, 92, 90, 88, 85, 84, 83, 82, 80, 78],
        "Platformă": ["OLX", "Autovit", "OLX", "OLX", "Autovit", "OLX", "Autovit", "OLX", "Autovit", "OLX"],
        "Preț (€)": [33000, 33500, 32800, 32750, 33600, 32900, 33700, 32600, 33400, 32500],
        "An fabricație": [2019, 2019, 2018, 2019, 2019, 2018, 2019, 2019, 2018, 2019],
        "KM": [50000, 52000, 48000, 51000, 53000, 49500, 52500, 50000, 54000, 50500],
        "Link": ["#"]*10
    })
    st.table(df_similar)

# ---------- TAB 3: Rezumat Zilnic ----------
with tab3:
    st.header("Rezumat Zilnic")
    st.write("Aici va fi afișat rezumatul emailului zilnic cu modificări de preț și listinguri noi.")

    df_email_summary = pd.DataFrame({
        "Mașină": ["BMW 530d", "Audi A6"],
        "Preț vechi (€)": [32200, 29100],
        "Preț nou (€)": [32000, 29000],
        "Schimbare (€)": [-200, -100],
        "Listing nou": ["Nu", "Da"]
    })
    st.table(df_email_summary)

    st.info("Emailul zilnic va conține aceleași informații ca tabelul de mai sus, cu statistici și oportunități.")
import sqlite3
import pandas as pd
# Citire date din baza de date
df = pd.read_sql_query("SELECT * FROM cars", conn)

# Filtrăm după model preferat (exemplu)
favorite_model = 'BMW 320i'
df_model = df[df['make'] + ' ' + df['model'] == favorite_model]

import plotly.express as px

# Grafic evoluție preț
fig = px.line(df_model, x='date', y='price', title=f'Evoluția prețului pentru {favorite_model}')
st.plotly_chart(fig)

# Conectare la baza de date
conn = sqlite3.connect('database/cars.db')
c = conn.cursor()

# Creare tabel dacă nu există
c.execute('''
CREATE TABLE IF NOT EXISTS cars (
    id INTEGER PRIMARY KEY,
    make TEXT,
    model TEXT,
    year INTEGER,
    mileage INTEGER,
    price REAL,
    date TEXT
)
''')
sample_data = [
    ('BMW', '320i', 2018, 50000, 18000, '2026-02-01'),
    ('BMW', '320i', 2018, 50000, 17800, '2026-02-02'),
    ('BMW', '320i', 2018, 50000, 17500, '2026-02-03'),
]

c.executemany('''
INSERT INTO cars (make, model, year, mileage, price, date)
VALUES (?, ?, ?, ?, ?, ?)
''', sample_data)
conn.commit()

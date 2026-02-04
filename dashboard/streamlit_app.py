import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os

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
# ---------------- PASSWORD END ----------------

# ---------------- DATABASE FUNCTION ----------------
def get_db_connection():
    # Creează folder database dacă nu există
    if not os.path.exists("database"):
        os.makedirs("database")

    # Conectare SQLite
    conn = sqlite3.connect("database/cars.db", check_same_thread=False)
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
    conn.commit()

    # Adaugă date sample dacă tabela e goală
    df_check = pd.read_sql_query("SELECT * FROM cars", conn)
    if df_check.empty:
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

    return conn

# ---------------- MAIN FUNCTION ----------------
def main():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM cars", conn)

    # Sidebar: selectare model favorit
    models = df['make'] + ' ' + df['model']
    models = models.unique().tolist()
    favorite_model = st.sidebar.selectbox("Selectează model favorit", models)

    df_model = df[df['make'] + ' ' + df['model'] == favorite_model]

    st.header(f"Evoluția prețului pentru {favorite_model}")
    fig = px.line(df_model, x='date', y='price', title=f'{favorite_model} – Evoluția prețului')
    st.plotly_chart(fig)

    st.subheader("Date brute")
    st.dataframe(df_model)

if __name__ == "__main__":
    main()

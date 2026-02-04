import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os

# ---------------- PASSWORD ----------------
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

# ---------------- DATABASE ----------------
def get_db_connection():
    if not os.path.exists("database"):
        os.makedirs("database")

    conn = sqlite3.connect("database/cars.db", check_same_thread=False)
    c = conn.cursor()
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

    # Date sample dacă tabela e goală
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
# ---------------- END DATABASE ----------------

# ---------------- MAIN ----------------
def main():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM cars", conn)

    # Sidebar: selectare model favorit
    models = (df['make'] + ' ' + df['model']).unique().tolist()
    favorite_model = st.sidebar.selectbox("Selectează model favorit", models)

    df_model = df[df['make'] + ' ' + df['model'] == favorite_model]

    # ---------------- TABURI ----------------
    tab1, tab2, tab3 = st.tabs(["Evoluție preț", "Date brute", "Mașini similare"])

    # Tab 1: Grafic evoluție
    with tab1:
        st.header(f"Evoluția prețului pentru {favorite_model}")
        fig = px.line(df_model, x='date', y='price', title=f'{favorite_model} – Evoluția prețului')
        st.plotly_chart(fig)

    # Tab 2: Tabel date brute
    with tab2:
        st.subheader("Date brute")
        st.dataframe(df_model)

    # Tab 3: Placeholder mașini similare OLX/Autovit
    with tab3:
        st.subheader("Mașini similare (OLX / Autovit)")
        st.info("Aici vor apărea mașinile similare în viitoarea integrare.")

if __name__ == "__main__":
    main()

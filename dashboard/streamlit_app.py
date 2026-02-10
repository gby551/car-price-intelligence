import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os

# ... (partea de password rămâne neschimbată) ...

def get_db_connection():
    # Folosim check_same_thread=False pentru Streamlit
    conn = sqlite3.connect("database/cars.db", check_same_thread=False)
    return conn

def main():
    st.set_page_config(page_title="Car Price Tracker", layout="wide") # Layout mai aerisit
    
    conn = get_db_connection()
    # Citim datele și convertim coloana date la format datetime
    df = pd.read_sql_query("SELECT * FROM cars", conn)
    df['date'] = pd.to_datetime(df['date'])

    if df.empty:
        st.warning("Baza de date este goală.")
        st.stop()

    # Sidebar cu branding și filtre
    st.sidebar.title("🚗 Car Analytics")
    
    # Filtru de Brand apoi Model (mai user-friendly)
    makes = df['make'].unique().tolist()
    selected_make = st.sidebar.selectbox("Marcă", makes)
    
    models = df[df['make'] == selected_make]['model'].unique().tolist()
    selected_model = st.sidebar.selectbox("Model", models)

    df_model = df[(df['make'] == selected_make) & (df['model'] == selected_model)]

    # ---------------- DASHBOARD ----------------
    st.title(f"Analiză Piață: {selected_make} {selected_model}")

    tab1, tab2, tab3 = st.tabs(["📈 Analiză Preț", "📋 Date Complete", "🔍 Predictor"])

    with tab1:
        # Indicatori rapizi
        c1, c2, c3 = st.columns(3)
        avg_price = df_model['price'].mean()
        latest_price = df_model.sort_values('date', ascending=False)['price'].iloc[0]
        
        c1.metric("Preț Mediu Actual", f"{avg_price:,.0f} €")
        c2.metric("Ultimul Preț Scanat", f"{latest_price:,.0f} €", 
                  delta=f"{latest_price - avg_price:,.0f} € față de medie", delta_color="inverse")
        c3.metric("Eșantion (Nr. mașini)", len(df_model))

        # Grafic evoluție medie zilnică (pentru a curăța zgomotul)
        st.subheader("Evoluția prețului în timp")
        df_daily = df_model.groupby('date')['price'].mean().reset_index()
        fig = px.line(df_daily, x='date', y='price', 
                     labels={'price': 'Preț Mediu (€)', 'date': 'Data Scanării'},
                     template="plotly_white")
        fig.update_traces(line_color='#ef4444', line_width=3)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Toate anunțurile identificate")
        # Adăugăm un filtru de sortare
        st.dataframe(df_model.sort_values('date', ascending=False), use_container_width=True)

    with tab3:
        st.subheader("Statistici de Vânzare (Estimat)")
        # Aici poți calcula diferența dintre prețul de listă și cel la care a dispărut
        st.info("Logica de detectare 'SOLD' va afișa aici prețul final de listare al mașinilor care au dispărut de pe site.")

if __name__ == "__main__":
    main()

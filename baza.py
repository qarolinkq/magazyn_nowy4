
      import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# 1. Połączenie z Supabase
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("Błąd konfiguracji Secrets w Streamlit Cloud!")
    st.stop()

st.set_page_config(page_title="Magazyn Pro WMS", layout="wide")

# --- FUNKCJE POMOCNICZE ---
def pobierz_dane():
    prod = supabase.table("Produkty").select("id, nazwa, liczba, cena, kategoria_id, kategorie(nazwa)").execute()
    kat = supabase.table("kategorie").select("id, nazwa").execute()
    return prod.data if prod.data else [], kat.data if kat.data else []

def usun_produkt(id_produktu):
    supabase.table("Produkty").delete().eq("id", id_produktu).execute()
    st.success("Produkt został usunięty.")
    st.rerun()

# Pobieranie danych
produkty_raw, kategorie_raw = pobierz_dane()
kat_dict = {k['nazwa']: k['id'] for k in kategorie_raw}

# --- PRZYGOTOWANIE RAMKI DANYCH (PANDAS) ---
if produkty_raw:
    df = pd.DataFrame(produkty_raw)
    # Wyciągamy nazwę kategorii z zagnieżdżonego słownika
    df['Kategoria'] = df['kategorie'].apply(lambda x: x['nazwa'] if isinstance(x, dict) else "Brak")
    df['Wartość'] = df['liczba'] * df['cena']
    df = df.rename(columns={'nazwa': 'Nazwa', 'liczba': 'Ilość', 'cena': 'Cena jednostkowa'})
else:
    df = pd.DataFrame()

# --- INTERFEJS ---
st.title("📦 Inteligentne Zarządzanie Magazynem")

tabs = st.tabs(["🏠 Magazyn", "📈 Raporty i Analiza", "➕ Dodaj Produkt"])

# --- TAB 1: MAGAZYN I USUWANIE ---
with tabs[0]:
    st.header("Aktualny stan magazynowy")
    if not df.empty:
        st.dataframe(df[['id', 'Nazwa', 'Ilość', 'Cena jednostkowa', 'Kategoria', 'Wartość']], use_container_width=True)
        
        st.subheader("🗑️ Usuwanie")
        col_del1, col_del2 = st.columns([3, 1])
        with col_del1:
            prod_to_del = st.selectbox("Wybierz produkt do usunięcia", produkty_raw, format_func=lambda x: f"{x['nazwa']} (ID: {x['id']})")
        with col_del2:
            st.write("##")
            if st.button("USUŃ", type="primary"):
                usun_produkt(prod_to_del['id'])
    else:
        st.info("Magazyn jest pusty.")

# --- TAB 2: RAPORTY I ANALIZA ---
with tabs[1]:
    if not df.empty:
        st.header("📊 Analiza szczegółowa")
        
        # Wskaźniki ogólne (KPI)
        m1, m2, m3 = st.columns(3)
        total_value = df['Wartość'].sum()
        total_items = df['Ilość'].sum()
        avg_price = df['Cena jednostkowa'].mean()
        
        m1.metric("Całkowita wartość magazynu", f"{total_value:,.2f} zł")
        m2.metric("Łączna liczba sztuk", f"{total_items} szt.")
        m3.metric("Średnia cena produktu", f"{avg_price:,.2f} zł")
        
        st.divider()
        
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Udział wartości wg kategorii")
            fig_pie = px.pie(df, values='Wartość', names='Kategoria', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with c2:
            st.subheader("Ilość produktów w kategoriach")
            fig_bar = px.bar(df.groupby('Kategoria')['Ilość'].sum().reset_index(), 
                             x='Kategoria', y='Ilość', color='Kategoria')
            st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()
        
        st.subheader("📄 Generowanie raportu")
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Pobierz raport CSV",
            data=csv,
            file_name='raport_magazynowy.csv',
            mime='text/csv',
        )
    else:
        st.warning("Brak danych do analizy.")

# --- TAB 3: DODAWANIE ---
with tabs[2]:
    st.header("➕ Dodaj nowy towar")
    nazwy_istniejace = df['Nazwa'].tolist() if not df.empty else []
    
    szukaj = st.selectbox("Podpowiedź (istniejące nazwy):", [""] + list(set(nazwy_istniejace)))
    
    with st.form("form_dodaj"):
        nowa_nazwa = st.text_input("Nazwa", value=szukaj)
        nowa_ilosc = st.number_input("Ilość", min_value=1)
        nowa_cena = st.number_input("Cena", min_value=0.0)
        wybrana_kat = st.selectbox("Kategoria", options=list(kat_dict.keys()))
        
        if st.form_submit_button("Zapisz"):
            nowy_rekord = {
                "nazwa": nowa_nazwa,
                "liczba": nowa_ilosc,
                "cena": nowa_cena,
                "kategoria_id": kat_dict[wybrana_kat]
            }
            supabase.table("Produkty").insert(nowy_rekord).execute()
            st.success("Dodano produkt!")
            st.rerun()

import streamlit as st
from supabase import create_client, Client
import pandas as pd

# Próba importu plotly - jeśli brakuje, aplikacja pokaże ostrzeżenie, ale zadziała
try:
    import plotly.express as px
except ImportError:
    px = None

# 1. Konfiguracja połączenia
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("Błąd konfiguracji Secrets!")
    st.stop()

st.set_page_config(page_title="WMS Magazyn", layout="wide")

# --- FUNKCJE BAZODANOWE ---
def pobierz_dane():
    try:
        # ZMIANA: Próbujemy pobrać dane. Jeśli Kategorie(nazwa) wywala błąd, 
        # spróbuj zmienić na kategorie(nazwa) małymi literami.
        prod = supabase.table("Produkty").select("id, nazwa, liczba, Cena, kategoria_id, Kategorie(nazwa)").execute()
        kat = supabase.table("Kategorie").select("id, nazwa").execute()
        return prod.data, kat.data
    except Exception as e:
        st.error(f"Błąd podczas pobierania danych: {e}")
        return [], []

def aktualizuj_stan(id_produktu, nowa_liczba):
    try:
        if nowa_liczba > 0:
            supabase.table("Produkty").update({"liczba": nowa_liczba}).eq("id", id_produktu).execute()
        else:
            supabase.table("Produkty").delete().eq("id", id_produktu).execute()
        st.rerun()
    except Exception as e:
        st.error(f"Błąd podczas aktualizacji: {e}")

# Pobranie danych
produkty_raw, kategorie_raw = pobierz_dane()

# Tworzenie słownika kategorii
kat_dict = {k['nazwa']: k['id'] for k in kategorie_raw} if kategorie_raw else {}
nazwy_istniejace = list(set([p['nazwa'] for p in produkty_raw])) if produkty_raw else []

st.title("📦 System Zarządzania Magazynem")

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["🏠 Stan i Wydawanie", "📈 Raporty", "➕ Przyjęcie Towaru"])

with tab1:
    if produkty_raw:
        for p in produkty_raw:
            with st.container():
                c1, c2, c3, c4 = st.columns([3, 1, 2, 1])
                c1.write(f"**{p['nazwa']}**")
                # Obsługa zagnieżdżonej nazwy kategorii
                kat_nazwa = p.get('Kategorie', {}).get('nazwa', 'Brak') if p.get('Kategorie') else "Brak"
                c1.caption(f"ID: {p['id']} | Kategoria: {kat_nazwa}")
                
                c2.write(f"{p['liczba']} szt.")
                
                ile_usunac = c3.number_input("Ile wydać?", min_value=1, max_value=int(p['liczba']), value=1, key=f"v_{p['id']}")
                
                if c4.button("Wydaj", key=f"b_{p['id']}"):
                    aktualizuj_stan(p['

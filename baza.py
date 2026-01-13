import streamlit as st
from supabase import create_client, Client

# Konfiguracja połączenia
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("Błąd konfiguracji Secrets! Sprawdź ustawienia na Streamlit Cloud.")
    st.stop()

st.title("📦 Panel Zarządzania Bazą")

# --- FUNKCJA POMOCNICZA DO OBSŁUGI BŁĘDÓW ---
def safe_execute(query_func):
    try:
        return query_func()
    except Exception as e:
        st.error(f"Szczegóły błędu: {e}")
        return None

# --- KATEGORIE ---
st.header("1. Kategorie")
nazwa_kat = st.text_input("Nazwa nowej kategorii")
if st.button("Dodaj Kategorię"):
    if nazwa_kat:
        # Zmieniono na małe litery: 'kategorie'
        safe_execute(lambda: supabase.table("kategorie").insert({"nazwa": nazwa_kat}).execute())
        st.success(f"Dodano kategorię: {nazwa_kat}")
        st.rerun()

# --- PRODUKTY ---
st.divider()
st.header("2. Produkty")

# Pobieranie kategorii (Używamy małych liter zgodnie z podpowiedzią błędu)
kat_data = safe_execute(lambda: supabase.table("kategorie").select("*").execute())
kategorie = kat_data.data if kat_data else []

if kategorie:
    kat_dict = {k['nazwa']: k['id'] for k in kategorie}
    
    with st.form("produkt_form"):
        nazwa_p = st.text_input("Nazwa produktu")
        ilosc = st.number_

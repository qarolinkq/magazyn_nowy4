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

# --- SEKCJA KATEGORII (Bez formularza dla prostoty) ---
st.header("1. Kategorie")
nazwa_kat = st.text_input("Nazwa nowej kategorii", key="new_kat_input")
if st.button("Dodaj Kategorię"):
    if nazwa_kat:
        safe_execute(lambda: supabase.table("kategorie").insert({"nazwa": nazwa_kat}).execute())
        st.success(f"Dodano kategorię: {nazwa_kat}")
        st.rerun()

st.divider()

# --- SEKCJA PRODUKTÓW (Z poprawnym formularzem) ---
st.header("2. Produkty")

# Pobieranie kategorii do listy wyboru
kat_data = safe_execute(lambda: supabase.table("kategorie").select("*").execute())
kategorie = kat_data.data if kat_data else []

if kategorie:
    kat_dict = {k['nazwa']: k['id'] for k in kategorie}
    
    # POCZĄTEK FORMULARZA
    with st.form("formularz_produktu"):
        nazwa_p = st.text_input("Nazwa produktu")
        ilosc = st.number_input("Liczba sztuk", min_value=0, step=1)
        # Zmienione na 'cena' (małymi) lub 'Ce...' zależnie od bazy
        cena = st.number_input("Cena", min_value=0.0, format="%.2f")
        wybrana_kat = st.selectbox("Wybierz kategorię", options=list(kat_dict.keys()))
        
        # PRZYCISK ZATWIERDZAJĄCY (Musi być wewnątrz bloku 'with st.form')
        submit_button = st.form_submit_button("Dodaj Produkt do Bazy")
        
        if submit_button:
            if nazwa_p:
                nowy_produkt = {
                    "nazwa": nazwa_p,
                    "liczba": ilosc,
                    "cena": cena, 
                    "kategoria_id": kat_dict

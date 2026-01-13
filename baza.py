import streamlit as st
from supabase import create_client, Client

# Konfiguracja połączenia
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("Błąd konfiguracji Secrets!")
    st.stop()

st.title("📦 Panel Zarządzania Bazą")

# --- FUNKCJA POMOCNICZA ---
def safe_execute(query_func):
    try:
        return query_func()
    except Exception as e:
        st.error(f"Błąd bazy: {e}")
        return None

# --- 1. KATEGORIE ---
st.header("1. Kategorie")
nazwa_kat = st.text_input("Nazwa nowej kategorii", key="kat_input")
if st.button("Dodaj Kategorię"):
    if nazwa_kat:
        safe_execute(lambda: supabase.table("kategorie").insert({"nazwa": nazwa_kat}).execute())
        st.success(f"Dodano: {nazwa_kat}")
        st.rerun()

st.divider()

# --- 2. PRODUKTY ---
st.header("2. Produkty")

# Pobieranie kategorii
kat_res = safe_execute(lambda: supabase.table("kategorie").select("*").execute())
kategorie = kat_res.data if kat_res else []

if kategorie:
    kat_dict = {k['nazwa']: k['id'] for k in kategorie}
    
    with st.form("produkt_form"):
        nazwa_p = st.text_input("Nazwa produktu")
        ilosc = st.number_input("Liczba", min_value=0, step=1)
        # UWAGA: Używamy 'cena' małymi literami zgodnie z poprzednią podpowiedzią bazy
        cena = st.number_input("Cena", min_value=0.0, format="%.2f")
        wybrana_kat = st.selectbox("Kategoria", options=list(kat_dict.keys()))
        
        submit = st.form_submit_button("Zapisz produkt")
        
        if submit:
            if nazwa_p:
                # Słownik poprawnie otwarty i zamknięty
                nowy_produkt = {
                    "nazwa": nazwa_p,
                    "liczba": ilosc,
                    "cena": cena,
                    "kategoria_id": kat_dict[wybrana_kat]
                }
                res = safe_execute(lambda: supabase.table("produkty").insert(nowy_produkt).execute())
                if res:
                    st.success("Dodano produkt!")
                    st.rerun()
